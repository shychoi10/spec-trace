"""
Full Parsing Test with Equation Extraction

기존 report_parser.py 로직을 기반으로 수식 추출 기능을 통합한 실험적 파서.
결과는 별도 폴더에 저장하여 기존 결과와 분리.

테스트 대상: RAN1-112
"""

import json
import zipfile
import xml.etree.ElementTree as ET
import tempfile
import subprocess
import os
import re
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional

# Namespaces
WORD_NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
MATH_NS = {'m': 'http://schemas.openxmlformats.org/officeDocument/2006/math'}

# Minimal DOCX template for equation conversion
CONTENT_TYPES_XML = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
    <Default Extension="xml" ContentType="application/xml"/>
    <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>'''

RELS_XML = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>'''

DOCUMENT_TEMPLATE = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
            xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math">
    <w:body>
        <w:p>
            {content}
        </w:p>
    </w:body>
</w:document>'''


@dataclass
class EquationInfo:
    """수식 정보"""
    plain_text: str
    latex: str
    position: int  # 단락 내 위치


@dataclass
class ParagraphContent:
    """단락 내용 (텍스트 + 수식 통합)"""
    raw_text: str  # 기존 방식 (수식 무시)
    text_with_equations: str  # 수식을 [EQUATION: ...] 마커로 표시
    latex_text: str  # 수식을 LaTeX로 변환
    equations: list = field(default_factory=list)
    has_equations: bool = False


@dataclass
class DecisionWithEquations:
    """수식 포함 Decision"""
    decision_id: str
    decision_type: str
    meeting_id: str
    agenda_item: str
    content_raw: str  # 기존 방식
    content_with_markers: str  # [EQUATION: ...] 마커
    content_latex: str  # LaTeX 변환
    equations: list = field(default_factory=list)
    paragraph_index: int = 0
    referenced_tdocs: list = field(default_factory=list)
    has_ffs: bool = False
    has_tbd: bool = False


class EquationExtractor:
    """수식 추출 및 변환 클래스"""

    def __init__(self):
        self._temp_dirs = []

    def extract_omml_text(self, omml_element) -> str:
        """OMML 요소에서 텍스트만 추출"""
        texts = []
        for t in omml_element.iter():
            if t.text:
                texts.append(t.text)
        return ''.join(texts)

    def omml_to_xml_string(self, omml_element) -> str:
        """OMML 요소를 XML 문자열로 변환"""
        ET.register_namespace('m', 'http://schemas.openxmlformats.org/officeDocument/2006/math')
        ET.register_namespace('w', 'http://schemas.openxmlformats.org/wordprocessingml/2006/main')
        return ET.tostring(omml_element, encoding='unicode')

    def create_temp_docx(self, omml_xml: str) -> Path:
        """수식만 포함하는 임시 DOCX 생성"""
        temp_dir = tempfile.mkdtemp()
        self._temp_dirs.append(temp_dir)
        temp_docx = Path(temp_dir) / "temp_equation.docx"

        with zipfile.ZipFile(temp_docx, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('[Content_Types].xml', CONTENT_TYPES_XML)
            zf.writestr('_rels/.rels', RELS_XML)
            doc_content = DOCUMENT_TEMPLATE.format(content=omml_xml)
            zf.writestr('word/document.xml', doc_content)

        return temp_docx

    def omml_to_latex(self, omml_element) -> str:
        """OMML 요소를 LaTeX로 변환"""
        omml_xml = self.omml_to_xml_string(omml_element)
        temp_docx = self.create_temp_docx(omml_xml)

        try:
            result = subprocess.run(
                ['pandoc', str(temp_docx), '-t', 'latex', '--wrap=none'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return f"[LATEX_ERROR: {result.stderr[:100]}]"
        except Exception as e:
            return f"[LATEX_ERROR: {str(e)[:100]}]"
        finally:
            try:
                os.unlink(temp_docx)
            except:
                pass

    def cleanup(self):
        """임시 디렉토리 정리"""
        for temp_dir in self._temp_dirs:
            try:
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
            except:
                pass
        self._temp_dirs = []


class HybridParagraphParser:
    """하이브리드 단락 파서 (python-docx 스타일 + lxml 수식 추출)"""

    def __init__(self):
        self.equation_extractor = EquationExtractor()

    def parse_paragraph(self, para_element) -> ParagraphContent:
        """단락에서 텍스트와 수식을 순서대로 추출"""
        parts_text = []
        parts_marker = []
        parts_latex = []
        equations = []
        has_equations = False
        eq_position = 0

        # 단락 내 모든 자식 요소 순회
        for child in para_element:
            tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag

            if tag == 'r':  # w:r (text run)
                # 텍스트 추출
                for t in child.findall('.//w:t', WORD_NS):
                    if t.text:
                        parts_text.append(t.text)
                        parts_marker.append(t.text)
                        parts_latex.append(t.text)

            elif tag == 'oMath':  # m:oMath (equation)
                has_equations = True
                plain_text = self.equation_extractor.extract_omml_text(child)
                latex = self.equation_extractor.omml_to_latex(child)

                equations.append(EquationInfo(
                    plain_text=plain_text,
                    latex=latex,
                    position=eq_position
                ))
                eq_position += 1

                # 각 버전에 추가
                parts_text.append(plain_text)  # 기존: 플레인 텍스트
                parts_marker.append(f" [EQ:{plain_text}] ")  # 마커 버전
                parts_latex.append(f" ${latex}$ ")  # LaTeX 버전

        return ParagraphContent(
            raw_text=''.join(parts_text).strip(),
            text_with_equations=''.join(parts_marker).strip(),
            latex_text=''.join(parts_latex).strip(),
            equations=[asdict(eq) for eq in equations],
            has_equations=has_equations
        )

    def cleanup(self):
        self.equation_extractor.cleanup()


class ExperimentalReportParser:
    """실험적 Report 파서 (수식 추출 통합)"""

    # Decision 패턴
    DECISION_PATTERNS = {
        'Agreement': re.compile(r'^Agreement[:\s]?', re.IGNORECASE),
        'Conclusion': re.compile(r'^Conclusion[:\s]?', re.IGNORECASE),
        'WorkingAssumption': re.compile(r'^Working\s*Assumption[:\s]?', re.IGNORECASE),
    }

    TDOC_PATTERN = re.compile(r'R1-\d{7}')
    FFS_PATTERN = re.compile(r'\bFFS\b', re.IGNORECASE)
    TBD_PATTERN = re.compile(r'\bTBD\b', re.IGNORECASE)
    ANNEX_PATTERN = re.compile(r'^Annex\s+[A-Z]', re.IGNORECASE)

    def __init__(self, docx_path: Path):
        self.docx_path = docx_path
        self.meeting_id = self._extract_meeting_id(docx_path)
        self.hybrid_parser = HybridParagraphParser()
        self.style_map = {}
        self.root = None

    def _extract_meeting_id(self, path: Path) -> str:
        """파일명에서 미팅 ID 추출"""
        match = re.search(r'RAN1[-_](\d+[a-z]?)', path.stem, re.IGNORECASE)
        if match:
            return f"RAN1#{match.group(1)}"
        return f"RAN1#{path.stem}"

    def _load_document(self):
        """문서 로드 및 스타일 맵 구축"""
        with zipfile.ZipFile(self.docx_path, 'r') as zf:
            # 스타일 로드
            try:
                with zf.open('word/styles.xml') as f:
                    styles_tree = ET.parse(f)
                    styles_root = styles_tree.getroot()

                    for style in styles_root.findall('.//w:style', WORD_NS):
                        style_id = style.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}styleId')
                        name_elem = style.find('w:name', WORD_NS)
                        if style_id and name_elem is not None:
                            val = name_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val', '')
                            self.style_map[style_id] = val.lower()
            except KeyError:
                pass

            # 문서 로드
            with zf.open('word/document.xml') as f:
                tree = ET.parse(f)
                self.root = tree.getroot()

    def _get_paragraph_style(self, para) -> str:
        """단락의 스타일 이름 가져오기"""
        pPr = para.find('w:pPr', WORD_NS)
        if pPr is not None:
            pStyle = pPr.find('w:pStyle', WORD_NS)
            if pStyle is not None:
                style_id = pStyle.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val', '')
                return self.style_map.get(style_id, style_id.lower())
        return 'normal'

    def parse(self) -> dict:
        """문서 파싱"""
        self._load_document()

        paragraphs_data = []
        decisions = []
        stats = {
            'total_paragraphs': 0,
            'paragraphs_with_equations': 0,
            'total_equations': 0,
            'decisions_with_equations': 0,
        }

        all_paras = self.root.findall('.//w:p', WORD_NS)
        stats['total_paragraphs'] = len(all_paras)

        # 1단계: 모든 단락 파싱
        for idx, para in enumerate(all_paras):
            style = self._get_paragraph_style(para)
            content = self.hybrid_parser.parse_paragraph(para)

            if content.has_equations:
                stats['paragraphs_with_equations'] += 1
                stats['total_equations'] += len(content.equations)

            paragraphs_data.append({
                'index': idx,
                'style': style,
                'raw_text': content.raw_text,
                'text_with_equations': content.text_with_equations,
                'latex_text': content.latex_text,
                'has_equations': content.has_equations,
                'equations': content.equations,
            })

        # 2단계: Decision 추출
        in_annex = False
        decision_counters = {}

        for idx, para_data in enumerate(paragraphs_data):
            text = para_data['raw_text']
            style = para_data['style']

            # TOC 스킵
            if style.startswith('toc'):
                continue

            # Annex 체크
            if self.ANNEX_PATTERN.match(text) and style.startswith('heading'):
                in_annex = True
                continue
            if in_annex:
                continue

            # Decision 패턴 매칭
            for decision_type, pattern in self.DECISION_PATTERNS.items():
                if pattern.match(text):
                    # content 추출 (다음 Decision/Heading까지)
                    content_parts_raw = []
                    content_parts_marker = []
                    content_parts_latex = []
                    all_equations = []

                    # 현재 단락의 내용 (키워드 제외)
                    current_text = pattern.sub('', text).strip()
                    if current_text:
                        content_parts_raw.append(current_text)
                        content_parts_marker.append(para_data['text_with_equations'])
                        content_parts_latex.append(para_data['latex_text'])
                        all_equations.extend(para_data['equations'])

                    # 다음 단락들 수집
                    for next_idx in range(idx + 1, len(paragraphs_data)):
                        next_para = paragraphs_data[next_idx]
                        next_text = next_para['raw_text']
                        next_style = next_para['style']

                        # 종료 조건
                        if next_style.startswith('heading'):
                            break
                        if any(p.match(next_text) for p in self.DECISION_PATTERNS.values()):
                            break
                        if self.ANNEX_PATTERN.match(next_text):
                            break

                        if next_text:
                            content_parts_raw.append(next_text)
                            content_parts_marker.append(next_para['text_with_equations'])
                            content_parts_latex.append(next_para['latex_text'])
                            all_equations.extend(next_para['equations'])

                    content_raw = '\n'.join(content_parts_raw)
                    content_marker = '\n'.join(content_parts_marker)
                    content_latex = '\n'.join(content_parts_latex)

                    if not content_raw.strip():
                        continue

                    # ID 생성
                    counter_key = decision_type
                    decision_counters[counter_key] = decision_counters.get(counter_key, 0) + 1
                    count = decision_counters[counter_key]

                    prefix_map = {
                        'Agreement': 'AGR',
                        'Conclusion': 'CON',
                        'WorkingAssumption': 'WA'
                    }
                    prefix = prefix_map.get(decision_type, 'DEC')
                    meeting_num = self.meeting_id.replace("RAN1#", "")
                    decision_id = f"{prefix}-{meeting_num}-{count:03d}"

                    decision = DecisionWithEquations(
                        decision_id=decision_id,
                        decision_type=decision_type,
                        meeting_id=self.meeting_id,
                        agenda_item="TBD",  # 간단한 테스트에서는 생략
                        content_raw=content_raw,
                        content_with_markers=content_marker,
                        content_latex=content_latex,
                        equations=all_equations,
                        paragraph_index=idx,
                        referenced_tdocs=self.TDOC_PATTERN.findall(content_raw),
                        has_ffs=bool(self.FFS_PATTERN.search(content_raw)),
                        has_tbd=bool(self.TBD_PATTERN.search(content_raw)),
                    )

                    if all_equations:
                        stats['decisions_with_equations'] += 1

                    decisions.append(asdict(decision))
                    break

        # 정리
        self.hybrid_parser.cleanup()

        return {
            'meeting_id': self.meeting_id,
            'docx_path': str(self.docx_path),
            'parsed_at': datetime.now().isoformat(),
            'stats': stats,
            'decisions': decisions,
            'sample_paragraphs_with_equations': [
                p for p in paragraphs_data if p['has_equations']
            ][:20],  # 샘플 20개만
        }


def main():
    """메인 실행"""
    # 테스트 파일
    docx_path = Path("/home/sihyeon/workspace/spec-trace/ontology/input/meetings/RAN1/Final_Report/Final_Report_RAN1-112.docx")

    # 출력 디렉토리 (기존과 분리)
    output_dir = Path("/home/sihyeon/workspace/spec-trace/scripts/experiments/equation-extraction/output")
    output_dir.mkdir(exist_ok=True)

    print(f"=" * 70)
    print(f"Experimental Report Parser with Equation Extraction")
    print(f"=" * 70)
    print(f"Input: {docx_path.name}")
    print(f"Output: {output_dir}")
    print()

    # 파싱
    print("Parsing document...")
    parser = ExperimentalReportParser(docx_path)
    result = parser.parse()

    # 결과 저장
    output_file = output_dir / f"parsed_{result['meeting_id'].replace('#', '_')}_with_equations.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\nResults saved to: {output_file}")

    # 통계 출력
    stats = result['stats']
    print(f"\n{'=' * 70}")
    print("PARSING STATISTICS")
    print(f"{'=' * 70}")
    print(f"Total paragraphs: {stats['total_paragraphs']}")
    print(f"Paragraphs with equations: {stats['paragraphs_with_equations']}")
    print(f"Total equations: {stats['total_equations']}")
    print(f"Total decisions: {len(result['decisions'])}")
    print(f"Decisions with equations: {stats['decisions_with_equations']}")

    # Decision 타입별 통계
    type_counts = {}
    for d in result['decisions']:
        dtype = d['decision_type']
        type_counts[dtype] = type_counts.get(dtype, 0) + 1

    print(f"\nDecision breakdown:")
    for dtype, count in sorted(type_counts.items()):
        print(f"  - {dtype}: {count}")

    # 수식 포함 Decision 샘플
    print(f"\n{'=' * 70}")
    print("SAMPLE DECISIONS WITH EQUATIONS")
    print(f"{'=' * 70}")

    decisions_with_eq = [d for d in result['decisions'] if d['equations']]
    for i, d in enumerate(decisions_with_eq[:5]):
        print(f"\n[{i+1}] {d['decision_id']} ({d['decision_type']})")
        print(f"    Equations: {len(d['equations'])}")
        print(f"    Raw (first 100 chars): {d['content_raw'][:100]}...")
        print(f"    LaTeX (first 150 chars): {d['content_latex'][:150]}...")
        if d['equations']:
            eq = d['equations'][0]
            print(f"    First equation: {eq['plain_text']} -> {eq['latex'][:80]}")

    # 수식 샘플
    print(f"\n{'=' * 70}")
    print("SAMPLE EQUATION CONVERSIONS")
    print(f"{'=' * 70}")

    all_equations = []
    for p in result['sample_paragraphs_with_equations']:
        all_equations.extend(p['equations'])

    unique_equations = {}
    for eq in all_equations:
        if eq['plain_text'] not in unique_equations:
            unique_equations[eq['plain_text']] = eq['latex']

    for i, (plain, latex) in enumerate(list(unique_equations.items())[:15]):
        print(f"  {plain:30} -> {latex[:50]}")

    print(f"\n{'=' * 70}")
    print("COMPARISON: Raw vs LaTeX")
    print(f"{'=' * 70}")

    # 동일 Decision의 raw vs latex 비교
    if decisions_with_eq:
        d = decisions_with_eq[0]
        print(f"\nDecision: {d['decision_id']}")
        print(f"\n[RAW VERSION]:")
        print(d['content_raw'][:500])
        print(f"\n[LATEX VERSION]:")
        print(d['content_latex'][:500])


if __name__ == "__main__":
    main()
