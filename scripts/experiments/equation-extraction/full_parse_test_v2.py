"""
Full Parsing Test with Equation Extraction - V2

개선 사항:
1. char_offset 추가 - 정확한 문자열 위치
2. 인라인/블록 수식 구분 - displayType 필드
3. 성능 최적화 - 배치 변환
4. 복잡 수식 fallback - 괄호 불균형 검증

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
from typing import Optional, List, Tuple
from concurrent.futures import ThreadPoolExecutor
import shutil

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
    """수식 정보 - V2"""
    plain_text: str
    latex: str
    position: int  # 단락 내 순서
    char_offset: int  # 문자열 내 시작 위치
    char_length: int  # plain_text 길이
    display_type: str  # 'inline' or 'block'
    is_valid: bool = True  # LaTeX 변환 성공 여부
    validation_note: str = ""  # 검증 메모


@dataclass
class ParagraphContent:
    """단락 내용 (텍스트 + 수식 통합)"""
    raw_text: str
    text_with_equations: str
    latex_text: str
    equations: list = field(default_factory=list)
    has_equations: bool = False


@dataclass
class DecisionWithEquations:
    """수식 포함 Decision"""
    decision_id: str
    decision_type: str
    meeting_id: str
    agenda_item: str
    content_raw: str
    content_with_markers: str
    content_latex: str
    equations: list = field(default_factory=list)
    paragraph_index: int = 0
    referenced_tdocs: list = field(default_factory=list)
    has_ffs: bool = False
    has_tbd: bool = False


class BatchEquationConverter:
    """배치 수식 변환기 - 성능 최적화"""

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self._temp_base = None

    def _setup_temp_dir(self):
        """임시 디렉토리 설정"""
        if self._temp_base is None:
            self._temp_base = Path(tempfile.mkdtemp())
        return self._temp_base

    def cleanup(self):
        """임시 디렉토리 정리"""
        if self._temp_base and self._temp_base.exists():
            shutil.rmtree(self._temp_base, ignore_errors=True)
        self._temp_base = None

    def _create_temp_docx(self, omml_xml: str, index: int) -> Path:
        """임시 DOCX 생성"""
        temp_dir = self._setup_temp_dir()
        temp_docx = temp_dir / f"eq_{index}.docx"

        with zipfile.ZipFile(temp_docx, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('[Content_Types].xml', CONTENT_TYPES_XML)
            zf.writestr('_rels/.rels', RELS_XML)
            doc_content = DOCUMENT_TEMPLATE.format(content=omml_xml)
            zf.writestr('word/document.xml', doc_content)

        return temp_docx

    def _convert_single(self, args: Tuple[int, str]) -> Tuple[int, str, bool, str]:
        """단일 수식 변환"""
        index, omml_xml = args
        temp_docx = self._create_temp_docx(omml_xml, index)

        try:
            result = subprocess.run(
                ['pandoc', str(temp_docx), '-t', 'latex', '--wrap=none'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                latex = result.stdout.strip()
                is_valid, note = self._validate_latex(latex)
                return (index, latex, is_valid, note)
            else:
                return (index, f"[ERROR: {result.stderr[:50]}]", False, "Pandoc error")
        except Exception as e:
            return (index, f"[ERROR: {str(e)[:50]}]", False, str(e))
        finally:
            try:
                os.unlink(temp_docx)
            except:
                pass

    def _validate_latex(self, latex: str) -> Tuple[bool, str]:
        """LaTeX 유효성 검증 - OMML boundary artifact 내성 강화"""
        import re as _re

        # Step 1: \left/\right delimiter 중립화
        # \left( 등의 괄호는 구분자(delimiter)이므로 그루핑 괄호와 분리하여 카운트
        cleaned = latex
        cleaned = _re.sub(r'\\left\s*[\(\[\{|.]', ' LDEL ', cleaned)
        cleaned = _re.sub(r'\\left\\[a-zA-Z]+', ' LDEL ', cleaned)
        cleaned = _re.sub(r'\\right\s*[\)\]\}|.]', ' RDEL ', cleaned)
        cleaned = _re.sub(r'\\right\\[a-zA-Z]+', ' RDEL ', cleaned)

        # Step 2: 괄호 유형별 불균형 계산
        p_diff = abs(cleaned.count('(') - cleaned.count(')'))
        b_diff = abs(cleaned.count('{') - cleaned.count('}'))
        k_diff = abs(cleaned.count('[') - cleaned.count(']'))

        # Step 3: OMML boundary artifact 허용
        # 3GPP DOCX에서 수식의 괄호가 일반 텍스트(w:r)와 OMML(m:oMath) 사이에
        # 분리되어 Pandoc 변환 시 괄호 짝이 안 맞을 수 있음
        # - paren: OMML 경계 영향 (≤5 허용)
        # - brace: LaTeX 구문 필수이므로 엄격 (≤1 허용)
        # - bracket: OMML 경계 영향 (≤1 허용)
        if p_diff > 5 or b_diff > 1 or k_diff > 1:
            return False, f"Unbalanced brackets: paren±{p_diff} brace±{b_diff} bracket±{k_diff}"

        # 에러 마커 검사
        if '[ERROR' in latex or latex.startswith('['):
            return False, "Contains error marker"

        if p_diff + b_diff + k_diff > 0:
            return True, f"OMML boundary artifact: paren±{p_diff} brace±{b_diff} bracket±{k_diff}"
        return True, ""

    def convert_batch(self, equations: List[Tuple[int, str]]) -> dict:
        """배치 변환 (병렬 처리)"""
        results = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = list(executor.map(self._convert_single, equations))

        for index, latex, is_valid, note in futures:
            results[index] = {
                'latex': latex,
                'is_valid': is_valid,
                'validation_note': note
            }

        return results


class HybridParagraphParserV2:
    """하이브리드 단락 파서 V2 - char_offset + display_type 지원"""

    def __init__(self):
        self.batch_converter = BatchEquationConverter()
        self._pending_equations = []  # (global_idx, omml_xml, para_idx, eq_idx, plain_text, display_type, char_offset)

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

    def _is_block_equation(self, element, parent_map: dict) -> bool:
        """블록 수식 여부 판단 (oMathPara 내부인지)"""
        parent = parent_map.get(element)
        if parent is not None:
            tag = parent.tag.split('}')[-1] if '}' in parent.tag else parent.tag
            if tag == 'oMathPara':
                return True
        return False

    def parse_paragraph_phase1(self, para_element, para_idx: int, parent_map: dict) -> dict:
        """1단계: 단락 파싱 (LaTeX 변환 없이 정보 수집)"""
        parts = []  # (type, content, display_type)
        equations_info = []
        current_offset = 0
        eq_position = 0

        for child in para_element:
            tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag

            if tag == 'r':  # w:r (text run)
                for t in child.findall('.//w:t', WORD_NS):
                    if t.text:
                        parts.append(('text', t.text, None))
                        current_offset += len(t.text)

            elif tag == 'oMath':  # m:oMath (equation)
                plain_text = self.extract_omml_text(child)
                omml_xml = self.omml_to_xml_string(child)
                display_type = 'block' if self._is_block_equation(child, parent_map) else 'inline'

                # 변환 대기열에 추가
                global_idx = len(self._pending_equations)
                self._pending_equations.append((
                    global_idx, omml_xml, para_idx, eq_position,
                    plain_text, display_type, current_offset
                ))

                parts.append(('equation', plain_text, display_type))
                equations_info.append({
                    'global_idx': global_idx,
                    'position': eq_position,
                    'plain_text': plain_text,
                    'char_offset': current_offset,
                    'char_length': len(plain_text),
                    'display_type': display_type,
                })

                current_offset += len(plain_text)
                eq_position += 1

            elif tag == 'oMathPara':  # 블록 수식 컨테이너
                for omath in child.findall('.//m:oMath', MATH_NS):
                    plain_text = self.extract_omml_text(omath)
                    omml_xml = self.omml_to_xml_string(omath)

                    global_idx = len(self._pending_equations)
                    self._pending_equations.append((
                        global_idx, omml_xml, para_idx, eq_position,
                        plain_text, 'block', current_offset
                    ))

                    parts.append(('equation', plain_text, 'block'))
                    equations_info.append({
                        'global_idx': global_idx,
                        'position': eq_position,
                        'plain_text': plain_text,
                        'char_offset': current_offset,
                        'char_length': len(plain_text),
                        'display_type': 'block',
                    })

                    current_offset += len(plain_text)
                    eq_position += 1

        # raw_text 생성
        raw_text = ''.join(p[1] for p in parts)

        return {
            'para_idx': para_idx,
            'parts': parts,
            'equations_info': equations_info,
            'raw_text': raw_text.strip(),
            'has_equations': len(equations_info) > 0,
        }

    def process_batch_conversion(self) -> dict:
        """2단계: 배치 LaTeX 변환"""
        if not self._pending_equations:
            return {}

        # 변환할 수식 준비
        to_convert = [(eq[0], eq[1]) for eq in self._pending_equations]

        # 배치 변환
        results = self.batch_converter.convert_batch(to_convert)

        # 결과 매핑
        conversion_map = {}
        for eq in self._pending_equations:
            global_idx = eq[0]
            conv_result = results.get(global_idx, {
                'latex': '[CONVERSION_FAILED]',
                'is_valid': False,
                'validation_note': 'Not found in results'
            })
            conversion_map[global_idx] = conv_result

        return conversion_map

    def finalize_paragraph(self, para_data: dict, conversion_map: dict) -> ParagraphContent:
        """3단계: 최종 단락 데이터 생성"""
        parts_text = []
        parts_marker = []
        parts_latex = []
        final_equations = []

        part_idx = 0
        eq_idx = 0

        for part_type, content, display_type in para_data['parts']:
            if part_type == 'text':
                parts_text.append(content)
                parts_marker.append(content)
                parts_latex.append(content)
            else:  # equation
                eq_info = para_data['equations_info'][eq_idx]
                global_idx = eq_info['global_idx']
                conv = conversion_map.get(global_idx, {
                    'latex': '[NO_CONVERSION]',
                    'is_valid': False,
                    'validation_note': 'Missing conversion'
                })

                parts_text.append(content)
                parts_marker.append(f" [EQ:{content}] ")

                # 블록 수식은 $$, 인라인은 $
                if display_type == 'block':
                    parts_latex.append(f"\n$${conv['latex']}$$\n")
                else:
                    parts_latex.append(f" ${conv['latex']}$ ")

                final_equations.append({
                    'plain_text': content,
                    'latex': conv['latex'],
                    'position': eq_info['position'],
                    'char_offset': eq_info['char_offset'],
                    'char_length': eq_info['char_length'],
                    'display_type': display_type,
                    'is_valid': conv['is_valid'],
                    'validation_note': conv['validation_note'],
                })

                eq_idx += 1

        return ParagraphContent(
            raw_text=para_data['raw_text'],
            text_with_equations=''.join(parts_marker).strip(),
            latex_text=''.join(parts_latex).strip(),
            equations=final_equations,
            has_equations=para_data['has_equations'],
        )

    def cleanup(self):
        self.batch_converter.cleanup()
        self._pending_equations = []


class ExperimentalReportParserV2:
    """실험적 Report 파서 V2"""

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
        self.parser = HybridParagraphParserV2()
        self.style_map = {}
        self.root = None

    def _extract_meeting_id(self, path: Path) -> str:
        match = re.search(r'RAN1[-_](\d+[a-z]?)', path.stem, re.IGNORECASE)
        if match:
            return f"RAN1#{match.group(1)}"
        return f"RAN1#{path.stem}"

    def _load_document(self):
        with zipfile.ZipFile(self.docx_path, 'r') as zf:
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

            with zf.open('word/document.xml') as f:
                tree = ET.parse(f)
                self.root = tree.getroot()

    def _get_paragraph_style(self, para) -> str:
        pPr = para.find('w:pPr', WORD_NS)
        if pPr is not None:
            pStyle = pPr.find('w:pStyle', WORD_NS)
            if pStyle is not None:
                style_id = pStyle.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val', '')
                return self.style_map.get(style_id, style_id.lower())
        return 'normal'

    def _build_parent_map(self) -> dict:
        """부모-자식 관계 맵 구축"""
        parent_map = {}
        for parent in self.root.iter():
            for child in parent:
                parent_map[child] = parent
        return parent_map

    def parse(self) -> dict:
        print("  Loading document...")
        self._load_document()

        parent_map = self._build_parent_map()
        all_paras = self.root.findall('.//w:p', WORD_NS)

        # 1단계: 모든 단락 파싱 (수식 수집)
        print(f"  Phase 1: Parsing {len(all_paras)} paragraphs...")
        para_data_list = []
        for idx, para in enumerate(all_paras):
            style = self._get_paragraph_style(para)
            para_data = self.parser.parse_paragraph_phase1(para, idx, parent_map)
            para_data['style'] = style
            para_data_list.append(para_data)

        # 2단계: 배치 LaTeX 변환
        pending_count = len(self.parser._pending_equations)
        print(f"  Phase 2: Converting {pending_count} equations in batch...")
        conversion_map = self.parser.process_batch_conversion()

        # 3단계: 최종 데이터 생성
        print("  Phase 3: Finalizing paragraphs...")
        paragraphs_final = []
        stats = {
            'total_paragraphs': len(all_paras),
            'paragraphs_with_equations': 0,
            'total_equations': 0,
            'valid_equations': 0,
            'invalid_equations': 0,
            'inline_equations': 0,
            'block_equations': 0,
            'decisions_with_equations': 0,
        }

        for para_data in para_data_list:
            content = self.parser.finalize_paragraph(para_data, conversion_map)

            if content.has_equations:
                stats['paragraphs_with_equations'] += 1
                stats['total_equations'] += len(content.equations)

                for eq in content.equations:
                    if eq['is_valid']:
                        stats['valid_equations'] += 1
                    else:
                        stats['invalid_equations'] += 1

                    if eq['display_type'] == 'inline':
                        stats['inline_equations'] += 1
                    else:
                        stats['block_equations'] += 1

            paragraphs_final.append({
                'index': para_data['para_idx'],
                'style': para_data['style'],
                'raw_text': content.raw_text,
                'text_with_equations': content.text_with_equations,
                'latex_text': content.latex_text,
                'has_equations': content.has_equations,
                'equations': content.equations,
            })

        # 4단계: Decision 추출
        print("  Phase 4: Extracting decisions...")
        decisions = self._extract_decisions(paragraphs_final, stats)

        # 정리
        self.parser.cleanup()

        return {
            'meeting_id': self.meeting_id,
            'docx_path': str(self.docx_path),
            'parsed_at': datetime.now().isoformat(),
            'version': 'v2.0',
            'stats': stats,
            'decisions': decisions,
            'sample_paragraphs_with_equations': [
                p for p in paragraphs_final if p['has_equations']
            ][:20],
        }

    def _recalculate_equation_offsets(self, equations: list, content_raw: str):
        """Decision 레벨에서 수식 position/char_offset 재계산

        단락별로 독립 계산된 position/char_offset을
        병합된 content_raw 기준으로 재매핑한다.
        단락 경계 공백 정규화도 수행.
        """
        search_start = 0
        for i, eq in enumerate(equations):
            # position: Decision 내 전역 순번
            eq['position'] = i

            # plain_text 정규화 (OMML 추출 시 선행/후행 공백 제거)
            plain = eq['plain_text'].strip()
            eq['plain_text'] = plain
            eq['char_length'] = len(plain)

            # char_offset: content_raw에서 plain_text의 실제 위치
            found_at = content_raw.find(plain, search_start)

            if found_at >= 0:
                eq['char_offset'] = found_at
                # 다음 검색은 이 위치 이후부터 (동일 수식 중복 대응)
                search_start = found_at + len(plain)
            # find 실패 시 기존 단락-로컬 값 유지 (fallback)

    def _extract_decisions(self, paragraphs: list, stats: dict) -> list:
        decisions = []
        in_annex = False
        decision_counters = {}

        for idx, para_data in enumerate(paragraphs):
            text = para_data['raw_text']
            style = para_data['style']

            if style.startswith('toc'):
                continue

            if self.ANNEX_PATTERN.match(text) and style.startswith('heading'):
                in_annex = True
                continue
            if in_annex:
                continue

            for decision_type, pattern in self.DECISION_PATTERNS.items():
                if pattern.match(text):
                    content_parts_raw = []
                    content_parts_marker = []
                    content_parts_latex = []
                    all_equations = []

                    current_text = pattern.sub('', text).strip()
                    if current_text:
                        content_parts_raw.append(current_text)
                        content_parts_marker.append(para_data['text_with_equations'])
                        content_parts_latex.append(para_data['latex_text'])
                        all_equations.extend(para_data['equations'])

                    for next_idx in range(idx + 1, len(paragraphs)):
                        next_para = paragraphs[next_idx]
                        next_text = next_para['raw_text']
                        next_style = next_para['style']

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

                    # Bug #1 fix: Decision 레벨에서 position/char_offset 재계산
                    if all_equations:
                        self._recalculate_equation_offsets(all_equations, content_raw)

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

                    if all_equations:
                        stats['decisions_with_equations'] += 1

                    decisions.append({
                        'decision_id': decision_id,
                        'decision_type': decision_type,
                        'meeting_id': self.meeting_id,
                        'agenda_item': "TBD",
                        'content_raw': content_raw,
                        'content_with_markers': content_marker,
                        'content_latex': content_latex,
                        'equations': all_equations,
                        'paragraph_index': idx,
                        'referenced_tdocs': self.TDOC_PATTERN.findall(content_raw),
                        'has_ffs': bool(self.FFS_PATTERN.search(content_raw)),
                        'has_tbd': bool(self.TBD_PATTERN.search(content_raw)),
                    })
                    break

        return decisions


def main():
    docx_path = Path("/home/sihyeon/workspace/spec-trace/ontology/input/meetings/RAN1/Final_Report/Final_Report_RAN1-112.docx")
    output_dir = Path("/home/sihyeon/workspace/spec-trace/scripts/experiments/equation-extraction/output")
    output_dir.mkdir(exist_ok=True)

    print("=" * 70)
    print("Experimental Report Parser V2 - Improved Equation Extraction")
    print("=" * 70)
    print(f"Input: {docx_path.name}")
    print()

    import time
    start_time = time.time()

    parser = ExperimentalReportParserV2(docx_path)
    result = parser.parse()

    elapsed = time.time() - start_time

    output_file = output_dir / f"parsed_{result['meeting_id'].replace('#', '_')}_with_equations_v2.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\nResults saved to: {output_file}")
    print(f"Elapsed time: {elapsed:.1f}s")

    stats = result['stats']
    print(f"\n{'=' * 70}")
    print("PARSING STATISTICS (V2)")
    print(f"{'=' * 70}")
    print(f"Total paragraphs: {stats['total_paragraphs']}")
    print(f"Paragraphs with equations: {stats['paragraphs_with_equations']}")
    print(f"Total equations: {stats['total_equations']}")
    print(f"  - Valid: {stats['valid_equations']}")
    print(f"  - Invalid: {stats['invalid_equations']}")
    print(f"  - Inline: {stats['inline_equations']}")
    print(f"  - Block: {stats['block_equations']}")
    print(f"Total decisions: {len(result['decisions'])}")
    print(f"Decisions with equations: {stats['decisions_with_equations']}")

    # 샘플 출력
    print(f"\n{'=' * 70}")
    print("SAMPLE: Equation with char_offset")
    print(f"{'=' * 70}")

    for d in result['decisions']:
        if d['equations']:
            print(f"\nDecision: {d['decision_id']}")
            for eq in d['equations'][:3]:
                print(f"  position={eq['position']}, offset={eq['char_offset']}, len={eq['char_length']}")
                print(f"    type={eq['display_type']}, valid={eq['is_valid']}")
                print(f"    plain: {eq['plain_text'][:40]}")
                print(f"    latex: {eq['latex'][:50]}")
            break

    # 유효성 검사 실패 케이스
    print(f"\n{'=' * 70}")
    print("INVALID EQUATIONS (if any)")
    print(f"{'=' * 70}")

    invalid_count = 0
    for d in result['decisions']:
        for eq in d['equations']:
            if not eq['is_valid']:
                print(f"  {d['decision_id']}: {eq['plain_text'][:30]}")
                print(f"    Note: {eq['validation_note']}")
                invalid_count += 1
                if invalid_count >= 5:
                    break
        if invalid_count >= 5:
            break

    if invalid_count == 0:
        print("  None found!")


if __name__ == "__main__":
    main()
