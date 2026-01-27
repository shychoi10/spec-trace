"""
Equation Extraction Prototype

하이브리드 방식 테스트:
1. python-docx로 단락/스타일 파싱 (기존 유지)
2. 단락 내 XML 요소 순회 (lxml)
3. w:r (텍스트) → 그대로 추출
4. m:oMath (수식) → 임시 DOCX 만들어서 Pandoc으로 LaTeX 변환
5. 순서대로 합쳐서 content에 저장
"""

import zipfile
import xml.etree.ElementTree as ET
import tempfile
import subprocess
import os
from pathlib import Path

# Namespaces
WORD_NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
MATH_NS = {'m': 'http://schemas.openxmlformats.org/officeDocument/2006/math'}
ALL_NS = {**WORD_NS, **MATH_NS}

# Minimal DOCX template parts
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


def count_equations_in_docx(docx_path: Path) -> dict:
    """DOCX 파일의 수식 통계 수집"""
    stats = {
        'total_paragraphs': 0,
        'paragraphs_with_equations': 0,
        'total_equations': 0,
        'equation_samples': []
    }

    with zipfile.ZipFile(docx_path, 'r') as zf:
        with zf.open('word/document.xml') as f:
            tree = ET.parse(f)
            root = tree.getroot()

    # Count paragraphs and equations
    for para in root.findall('.//w:p', WORD_NS):
        stats['total_paragraphs'] += 1
        equations = para.findall('.//m:oMath', MATH_NS)
        if equations:
            stats['paragraphs_with_equations'] += 1
            stats['total_equations'] += len(equations)

            # Sample first 5 equations
            if len(stats['equation_samples']) < 5:
                for eq in equations[:3]:
                    eq_text = extract_omml_text(eq)
                    if eq_text:
                        stats['equation_samples'].append(eq_text[:100])

    return stats


def extract_omml_text(omml_element) -> str:
    """OMML 요소에서 텍스트만 추출 (간단한 방식)"""
    texts = []
    for t in omml_element.iter():
        if t.text:
            texts.append(t.text)
    return ''.join(texts)


def omml_to_xml_string(omml_element) -> str:
    """OMML 요소를 XML 문자열로 변환"""
    # Register namespaces to avoid ns0, ns1 prefixes
    ET.register_namespace('m', 'http://schemas.openxmlformats.org/officeDocument/2006/math')
    ET.register_namespace('w', 'http://schemas.openxmlformats.org/wordprocessingml/2006/main')

    return ET.tostring(omml_element, encoding='unicode')


def create_temp_docx_with_equation(omml_xml: str) -> Path:
    """수식만 포함하는 임시 DOCX 파일 생성"""
    temp_dir = tempfile.mkdtemp()
    temp_docx = Path(temp_dir) / "temp_equation.docx"

    # Create DOCX structure
    with zipfile.ZipFile(temp_docx, 'w', zipfile.ZIP_DEFLATED) as zf:
        # [Content_Types].xml
        zf.writestr('[Content_Types].xml', CONTENT_TYPES_XML)

        # _rels/.rels
        zf.writestr('_rels/.rels', RELS_XML)

        # word/document.xml with the equation
        doc_content = DOCUMENT_TEMPLATE.format(content=omml_xml)
        zf.writestr('word/document.xml', doc_content)

    return temp_docx


def convert_docx_to_latex_via_pandoc(docx_path: Path) -> str:
    """Pandoc으로 DOCX를 LaTeX로 변환"""
    try:
        result = subprocess.run(
            ['pandoc', str(docx_path), '-t', 'latex', '--wrap=none'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"[PANDOC_ERROR: {result.stderr}]"
    except FileNotFoundError:
        return "[PANDOC_NOT_INSTALLED]"
    except subprocess.TimeoutExpired:
        return "[PANDOC_TIMEOUT]"
    except Exception as e:
        return f"[ERROR: {str(e)}]"


def omml_to_latex(omml_element) -> str:
    """OMML 요소를 LaTeX로 변환"""
    # 1. OMML을 XML 문자열로
    omml_xml = omml_to_xml_string(omml_element)

    # 2. 임시 DOCX 생성
    temp_docx = create_temp_docx_with_equation(omml_xml)

    try:
        # 3. Pandoc으로 변환
        latex = convert_docx_to_latex_via_pandoc(temp_docx)
        return latex
    finally:
        # 4. 정리
        try:
            os.unlink(temp_docx)
            os.rmdir(temp_docx.parent)
        except:
            pass


def extract_paragraph_with_equations(para_element) -> dict:
    """단락에서 텍스트와 수식을 순서대로 추출"""
    parts = []
    has_equation = False

    # 단락 내 모든 자식 요소 순회
    for child in para_element:
        tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag

        if tag == 'r':  # w:r (text run)
            # 텍스트 추출
            text_elem = child.find('.//w:t', WORD_NS)
            if text_elem is not None and text_elem.text:
                parts.append({'type': 'text', 'content': text_elem.text})

        elif tag == 'oMath':  # m:oMath (equation)
            has_equation = True
            # 수식을 LaTeX로 변환
            latex = omml_to_latex(child)
            plain_text = extract_omml_text(child)
            parts.append({
                'type': 'equation',
                'latex': latex,
                'plain': plain_text
            })

    # 합치기
    combined_text = ""
    combined_latex = ""
    for part in parts:
        if part['type'] == 'text':
            combined_text += part['content']
            combined_latex += part['content']
        else:
            combined_text += f" [{part['plain']}] "
            combined_latex += f" ${part['latex']}$ "

    return {
        'has_equation': has_equation,
        'parts': parts,
        'combined_text': combined_text.strip(),
        'combined_latex': combined_latex.strip()
    }


def test_single_equation(docx_path: Path) -> dict:
    """단일 수식 변환 테스트"""
    print(f"\n{'='*60}")
    print(f"Testing: {docx_path.name}")
    print(f"{'='*60}")

    # 1. 수식 통계
    stats = count_equations_in_docx(docx_path)
    print(f"\n📊 Statistics:")
    print(f"  - Total paragraphs: {stats['total_paragraphs']}")
    print(f"  - Paragraphs with equations: {stats['paragraphs_with_equations']}")
    print(f"  - Total equations: {stats['total_equations']}")

    if stats['total_equations'] == 0:
        print("\n⚠️ No equations found in this document")
        return stats

    print(f"\n📝 Sample equation texts (plain):")
    for i, sample in enumerate(stats['equation_samples'], 1):
        print(f"  {i}. {sample}")

    # 2. 실제 변환 테스트
    print(f"\n🔄 Testing LaTeX conversion...")

    with zipfile.ZipFile(docx_path, 'r') as zf:
        with zf.open('word/document.xml') as f:
            tree = ET.parse(f)
            root = tree.getroot()

    # 첫 번째 수식 찾기
    first_equation = root.find('.//m:oMath', MATH_NS)
    if first_equation is not None:
        print(f"\n  Original OMML text: {extract_omml_text(first_equation)[:80]}")

        latex_result = omml_to_latex(first_equation)
        print(f"  Converted LaTeX: {latex_result[:200]}")

        stats['latex_conversion_result'] = latex_result

    # 3. 수식 포함 단락 테스트
    print(f"\n📄 Testing paragraph extraction with equations...")

    tested_count = 0
    for para in root.findall('.//w:p', WORD_NS):
        if para.findall('.//m:oMath', MATH_NS):
            result = extract_paragraph_with_equations(para)
            if result['has_equation'] and tested_count < 2:
                print(f"\n  Paragraph {tested_count + 1}:")
                print(f"    Combined text: {result['combined_text'][:100]}...")
                print(f"    Combined LaTeX: {result['combined_latex'][:100]}...")
                tested_count += 1

    return stats


def main():
    """메인 실행"""
    # Final Report 경로
    final_report_dir = Path("/home/sihyeon/workspace/spec-trace/ontology/input/meetings/RAN1/Final_Report")

    # Pandoc 설치 확인
    print("🔍 Checking pandoc installation...")
    try:
        result = subprocess.run(['pandoc', '--version'], capture_output=True, text=True)
        print(f"  ✅ Pandoc installed: {result.stdout.split(chr(10))[0]}")
    except FileNotFoundError:
        print("  ❌ Pandoc not installed!")
        print("  Please install: sudo apt install pandoc")
        return

    # 테스트할 파일 선택 (수식이 많을 것 같은 최근 회의)
    test_files = [
        final_report_dir / "Final_Report_RAN1-112.docx",
        final_report_dir / "Final_Report_RAN1-100.docx",
    ]

    results = {}
    for test_file in test_files:
        if test_file.exists():
            results[test_file.name] = test_single_equation(test_file)
            break  # 첫 번째 파일만 테스트
        else:
            print(f"⚠️ File not found: {test_file}")

    # 결과 요약
    print(f"\n{'='*60}")
    print("📋 SUMMARY")
    print(f"{'='*60}")

    for filename, stats in results.items():
        print(f"\n{filename}:")
        print(f"  - Equations: {stats.get('total_equations', 0)}")
        print(f"  - Paragraphs with equations: {stats.get('paragraphs_with_equations', 0)}")
        if 'latex_conversion_result' in stats:
            success = not stats['latex_conversion_result'].startswith('[')
            print(f"  - LaTeX conversion: {'✅ Success' if success else '❌ Failed'}")


if __name__ == "__main__":
    main()
