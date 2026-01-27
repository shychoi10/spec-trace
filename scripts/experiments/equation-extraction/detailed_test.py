"""
상세 수식 변환 테스트

더 복잡한 수식이 어떻게 변환되는지 확인
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

# Minimal DOCX template
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


def extract_omml_text(omml_element) -> str:
    """OMML 요소에서 텍스트만 추출"""
    texts = []
    for t in omml_element.iter():
        if t.text:
            texts.append(t.text)
    return ''.join(texts)


def omml_to_xml_string(omml_element) -> str:
    """OMML 요소를 XML 문자열로 변환"""
    ET.register_namespace('m', 'http://schemas.openxmlformats.org/officeDocument/2006/math')
    ET.register_namespace('w', 'http://schemas.openxmlformats.org/wordprocessingml/2006/main')
    return ET.tostring(omml_element, encoding='unicode')


def create_temp_docx_with_equation(omml_xml: str) -> Path:
    """수식만 포함하는 임시 DOCX 파일 생성"""
    temp_dir = tempfile.mkdtemp()
    temp_docx = Path(temp_dir) / "temp_equation.docx"

    with zipfile.ZipFile(temp_docx, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('[Content_Types].xml', CONTENT_TYPES_XML)
        zf.writestr('_rels/.rels', RELS_XML)
        doc_content = DOCUMENT_TEMPLATE.format(content=omml_xml)
        zf.writestr('word/document.xml', doc_content)

    return temp_docx


def omml_to_latex(omml_element) -> str:
    """OMML 요소를 LaTeX로 변환"""
    omml_xml = omml_to_xml_string(omml_element)
    temp_docx = create_temp_docx_with_equation(omml_xml)

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
            return f"[ERROR: {result.stderr}]"
    except Exception as e:
        return f"[ERROR: {str(e)}]"
    finally:
        try:
            os.unlink(temp_docx)
            os.rmdir(temp_docx.parent)
        except:
            pass


def main():
    """다양한 수식 테스트"""
    docx_path = Path("/home/sihyeon/workspace/spec-trace/ontology/input/meetings/RAN1/Final_Report/Final_Report_RAN1-112.docx")

    with zipfile.ZipFile(docx_path, 'r') as zf:
        with zf.open('word/document.xml') as f:
            tree = ET.parse(f)
            root = tree.getroot()

    # 모든 수식 찾기
    all_equations = root.findall('.//m:oMath', MATH_NS)

    print(f"총 수식 개수: {len(all_equations)}")
    print(f"\n{'='*80}")
    print("수식 변환 샘플 (처음 20개)")
    print(f"{'='*80}")

    # 다양한 수식 샘플 테스트
    unique_equations = {}
    for eq in all_equations:
        plain_text = extract_omml_text(eq)
        if plain_text and plain_text not in unique_equations:
            unique_equations[plain_text] = eq

    print(f"\n고유 수식 개수: {len(unique_equations)}")

    tested = 0
    for plain_text, eq in list(unique_equations.items())[:20]:
        latex = omml_to_latex(eq)

        print(f"\n[{tested + 1}]")
        print(f"  Plain text: {plain_text}")
        print(f"  LaTeX:      {latex}")

        tested += 1

    # 복잡한 수식 찾기 (길이로 판단)
    print(f"\n{'='*80}")
    print("복잡한 수식 (길이 > 10)")
    print(f"{'='*80}")

    complex_count = 0
    for plain_text, eq in unique_equations.items():
        if len(plain_text) > 10:
            latex = omml_to_latex(eq)
            print(f"\n[Complex {complex_count + 1}]")
            print(f"  Plain text: {plain_text}")
            print(f"  LaTeX:      {latex}")
            complex_count += 1
            if complex_count >= 10:
                break


if __name__ == "__main__":
    main()
