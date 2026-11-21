from django.core.cache import cache
from rest_framework.exceptions import NotFound
from io import BytesIO
from collections import defaultdict
from config import settings
from datetime import datetime

from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import (
    Font,
    Alignment,
    Border,
    Side,
    PatternFill
)

from django.db.models import Count, Q

from docx import Document
from docx.enum.text import WD_BREAK, WD_ALIGN_PARAGRAPH
from docx.shared import Pt
from docxtpl import DocxTemplate
from docxcompose.composer import Composer

from apps.api.models import Log, WorkingUnit
from apps.kinerja.models import PerformanceIndicators, PerformanceTargets, AchievementTarget, PerformanceDocument

def create_log(user, action, feature_name, message):
    log = Log.objects.create(user=user, action=action, feature_name=feature_name, message=message)
    return log

METHOD_MAP = {
    "Rata-rata": ("semester_satu_rata_rata", "tw_tiga_rata_rata", "semester_dua_rata_rata"),
    "Posisi Akhir": ("semester_satu_posisi_akhir", "tw_tiga_posisi_akhir", "semester_dua_posisi_akhir"),
    "Akumulasi": ("semester_satu_akumulasi", "tw_tiga_akumulasi", "semester_dua_akumulasi"),
}

def _get_derived_values(achievement_target, calculation_data):
    methods = METHOD_MAP.get(calculation_data, METHOD_MAP["Posisi Akhir"])
    smt1_method, tw3_method, tw4_method = methods

    smt1   = getattr(achievement_target, smt1_method)()
    sd_tw3 = getattr(achievement_target, tw3_method)()
    sd_tw4 = getattr(achievement_target, tw4_method)()

    return (
        float(smt1) if smt1 is not None else None,
        float(sd_tw3) if sd_tw3 is not None else None,
        float(sd_tw4) if sd_tw4 is not None else None,
    )

def get_unker_ids_bfs(unit_kerja_id, sync_data=False):
    """Get data unker with BFS (Breadth-First Search)."""

    key = f"list_unker_bfs_{unit_kerja_id}"
    if not sync_data:
        cache_data = cache.get(key)

        if cache_data:
            return cache_data

    current = WorkingUnit.objects.filter(id=unit_kerja_id, is_delete=False).first()

    if not current:
        return []

    result = []
    result = [current.code]    
    visited = {current.code}

    current_level = [current]

    while current_level:
        next_level = []

        for parent in current_level:
            children = WorkingUnit.objects.filter(parent=parent, is_delete=False)

            for child in children:
                if not child.code:
                    continue

                if child.code in visited:
                    continue

                visited.add(child.code)
                next_level.append(child)
        next_level.sort(
            key=lambda x: x.code
        )

        result.extend(
            child.code
            for child in next_level
        )

        current_level = next_level
    if result:
        cache.set(key, result)
    return result

MONTHS = ["jan", "feb", "mar", "apr", "mei", "jun", "jul", "agu", "sep", "okt", "nov", "des"]

PERIODE_MONTHS = {
    "tw1": MONTHS[0:3],
    "tw2": MONTHS[3:6],
    "tw3": MONTHS[6:9],
    "tw4": MONTHS[9:12],
}

def export_matrix_target(unker_id, year):
    queryset = PerformanceIndicators.objects.filter(is_delete=False, year=year)

    if not unker_id:
        raise NotFound(detail="Unit Kerja not found")

    parent = WorkingUnit.objects.get(id=unker_id, is_delete=False)
    if parent:
        children = WorkingUnit.objects.filter(parent=parent)

    queryset = queryset.filter(unker__in=[parent, *children])

    workbook = Workbook()
    ws = workbook.active
    ws.title = "Sheet1"

    bold_font = Font(bold=True, size=10)

    center = Alignment(
        horizontal='center',
        vertical='center',
        wrap_text=True
    )

    left = Alignment(
        horizontal='left',
        vertical='top',
        wrap_text=True
    )

    normal_font = Font(size=10)

    thin = Side(
        style='thin',
        color='000000'
    )

    border = Border(
        left=thin,
        right=thin,
        top=thin,
        bottom=thin
    )

    ws['A1'] = 'RINCIAN TARGET IKU'
    ws['A1'].font = bold_font

    ws['A2'] = 'UNIT KERJA'
    ws['B2'] = parent.name
    ws['A3'] = 'TAHUN'
    ws['B3'] = year

    ws.merge_cells('A5:A6')
    ws.merge_cells('B5:B6')
    ws.merge_cells('C5:C6')
    ws.merge_cells('D5:D6')
    ws.merge_cells('E5:E6')
    ws.merge_cells('F5:L5')
    ws.merge_cells('M5:M6')

    ws['A5'] = 'NO'
    ws['B5'] = 'INDIKATOR KINERJA UTAMA'
    ws['C5'] = 'SATUAN'
    ws['D5'] = 'POLA HITUNG'
    ws['E5'] = 'FREKUENSI PERHITUNGAN'
    ws['F5'] = 'TARGET'
    ws['M5'] = f'TARGET {year}'

    ws['F5'].alignment = center

    sub_headers = [
        'TW I',
        'TW II',
        'SMT I',
        'TW III',
        's/d TW III',
        'TW IV',
        's/d TW IV'
    ]

    start_col = 6  # F

    for index, title in enumerate(sub_headers):
        cell = ws.cell(row=6, column=start_col + index)
        cell.value = title
        cell.font = bold_font
        cell.alignment = center
        cell.border = border

    header_cells = [
        'A5', 'B5', 'C5', 'D5', 'E5', 'F5', 'M5'
    ]

    for cell_name in header_cells:
        cell = ws[cell_name]
        cell.font = bold_font
        cell.alignment = center
        cell.border = border

    row_num = 7

    for index, item in enumerate(queryset.iterator(), start=1):

        ws.cell(row=row_num, column=1, value=index)
        ws.cell(row=row_num, column=2, value=item.title)
        ws.cell(row=row_num, column=3, value=item.unit)
        ws.cell(row=row_num, column=4, value=item.calculation_data)
        ws.cell(row=row_num, column=5, value=item.period)

        data_target = AchievementTarget.objects.filter(
            indicator=item, category="Performance Indicator"
        ).first()

        if not data_target:
            row_num += 1
            continue

        tw1 = float(data_target.tw1) if data_target.tw1 is not None else 0.0
        tw2 = float(data_target.tw2) if data_target.tw2 is not None else 0.0
        tw3 = float(data_target.tw3) if data_target.tw3 is not None else 0.0
        tw4 = float(data_target.tw4) if data_target.tw4 is not None else 0.0

        smt1, sd_tw3, sd_tw4 = _get_derived_values(data_target, item.calculation_data)

        ws.cell(row=row_num, column=6, value=tw1)
        ws.cell(row=row_num, column=7, value=tw2)
        ws.cell(row=row_num, column=8, value=smt1)
        ws.cell(row=row_num, column=9, value=tw3)
        ws.cell(row=row_num, column=10, value=sd_tw3)
        ws.cell(row=row_num, column=11, value=tw4)
        ws.cell(row=row_num, column=12, value=sd_tw4)
        ws.cell(row=row_num, column=13, value=item.target)

        center_columns = [1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]

        for col in range(1, 14):
            cell = ws.cell(row=row_num, column=col)
            cell.font = normal_font
            cell.alignment = center if col in center_columns else left
            cell.border = border

        row_num += 1


    for col in range(1, ws.max_column + 1):
        header_1 = ws.cell(row=5, column=col).value
        header_2 = ws.cell(row=6, column=col).value

        max_length = max(
            len(str(header_1 or '')),
            len(str(header_2 or ''))
        )

        column_letter = get_column_letter(col)

        ws.column_dimensions[column_letter].width = max_length + 5

    excel_file = BytesIO()
    workbook.save(excel_file)
    excel_file.seek(0)

    return excel_file

def export_rincian_indikator(unker_id, year, unker_nama):
    queryset = PerformanceIndicators.objects.filter(is_delete=False, year=year)

    if not unker_id:
        raise NotFound(detail="Unit Kerja not found")

    queryset = queryset.filter(unker__id__in=unker_id,is_delete=False).order_by('unker__level', 'unker__code')

    workbook = Workbook()
    ws = workbook.active
    ws.title = "Sheet1"

    bold_font = Font(bold=True, size=10)

    center = Alignment(
        horizontal='center',
        vertical='center',
        wrap_text=True
    )

    # FONT
    bold_font = Font(bold=True, name='Liberation Serif', size=10)
    normal_font = Font(name='Liberation Serif', size=10)

    # ALIGNMENT
    center = Alignment(horizontal='center', vertical='center', wrap_text=True)
    left = Alignment(horizontal='left', vertical='center', wrap_text=True)

    # BORDER
    thin = Side(style='thin', color='000000')
    border = Border(
        left=thin,
        right=thin,
        top=thin,
        bottom=thin
    )

    # TITLE
    ws['A2'] = 'DAFTAR INDIKATOR KINERJA'
    ws['A2'].font = bold_font

    ws['A3'] = 'Unit Kerja'
    ws['A3'].alignment = left
    ws['B3'] = unker_nama.upper()
    ws['B3'].font = normal_font
    ws['B3'].alignment = left

    # HEADER
    headers = [
        'No', 
        'Unit Kerja', 
        'Tahun', 
        'Indikator Kinerja Atasan',
        'Sasaran', 
        'Indikator Kinerja', 
        'Definisi', 
        'Metode Pengukuran', 
        'Sumber Data', 
        'Tingkat Validitas', 
        'Polarisasi', 
        'Status', 
        'Jenis', 
        'Satuan', 
        'Pola Perhitungan', 
        'Periode Pelaporan', 
        'Metode Cascading', 
        'Batas Atas', 
        'Batas Bawah', 
        'Sisa Breakdown' 
    ]

    target_headers = [
        'Tahunan',
        'TW 1',
        'TW 2',
        'TW 3',
        'TW 4',
    ]

    additional_headers = [
        'Cascading'
    ]

    # ROW HEADER
    header_row_1 = 5
    header_row_2 = 6

    # HEADER UTAMA
    for idx, title in enumerate(headers, start=1):
        col = get_column_letter(idx)

        ws.merge_cells(f'{col}{header_row_1}:{col}{header_row_2}')

        cell = ws[f'{col}{header_row_1}']
        cell.value = title
        cell.font = bold_font
        cell.alignment = center
        cell.border = border

    # TARGET HEADER
    target_start_col = len(headers) + 1

    target_end_col = target_start_col + len(target_headers) - 1

    ws.merge_cells(
        start_row=header_row_1,
        start_column=target_start_col,
        end_row=header_row_1,
        end_column=target_end_col
    )

    cell = ws.cell(row=header_row_1, column=target_start_col)
    cell.value = 'Target'
    cell.font = bold_font
    cell.alignment = center
    cell.border = border

    for idx, title in enumerate(target_headers):
        cell = ws.cell(
            row=header_row_2,
            column=target_start_col + idx
        )

        cell.value = title
        cell.font = bold_font
        cell.alignment = center
        cell.border = border

    # HEADER TAMBAHAN
    additional_start_col = target_end_col + 1

    for idx, title in enumerate(additional_headers):
        col_num = additional_start_col + idx
        col = get_column_letter(col_num)

        ws.merge_cells(f'{col}{header_row_1}:{col}{header_row_2}')

        cell = ws[f'{col}{header_row_1}']
        cell.value = title
        cell.font = bold_font
        cell.alignment = center
        cell.border = border

    row_num = 7
    for index, item in enumerate(queryset, start=1):
        for col in range(1, 51):
            ws.cell(row=row_num, column=col).font = normal_font
            
        ws.cell(row=row_num, column=1, value=index)
        ws.cell(row=row_num, column=2, value=item.unker.name if item.unker else None)
        ws.cell(row=row_num, column=3, value=item.year)
        ws.cell(row=row_num, column=4, value=item.reference_indicator.title if item.reference_indicator else None)
        ws.cell(row=row_num, column=5, value=item.performance_targets.title if item.performance_targets else None)
        ws.cell(row=row_num, column=6, value=item.title)
        ws.cell(row=row_num, column=7, value=item.definition)
        ws.cell(row=row_num, column=8, value=item.calculation_method)
        ws.cell(row=row_num, column=9, value=item.data_source)
        ws.cell(row=row_num, column=10, value=item.validity)
        ws.cell(row=row_num, column=11, value=item.polarization)
        ws.cell(row=row_num, column=12, value=item.state)
        ws.cell(row=row_num, column=13, value=item.type)
        ws.cell(row=row_num, column=14, value=item.unit)
        ws.cell(row=row_num, column=15, value=item.calculation_data)
        ws.cell(row=row_num, column=16, value=item.period)
        ws.cell(row=row_num, column=17, value=item.cascading_method)
        ws.cell(row=row_num, column=18, value=item.upper_limit)
        ws.cell(row=row_num, column=19, value=item.lower_limit)
        ws.cell(row=row_num, column=20, value=item.remaining_breakdown)

        data_target = AchievementTarget.objects.filter(indicator=item, category="Performance Indicator").first()

        if not data_target:
            row_num += 1
            continue

        tw1 = float(data_target.tw1) if data_target.tw1 else None
        tw2 = float(data_target.tw2) if data_target.tw2 else None
        tw3 = float(data_target.tw3) if data_target.tw3 else None
        tw4 = float(data_target.tw4) if data_target.tw4 else None

        smt1, sd_tw3, sd_tw4 = _get_derived_values(data_target, item.calculation_data)

        # target
        ws.cell(row=row_num, column=21, value=item.target if item.target else None)
        ws.cell(row=row_num, column=22, value=tw1)
        ws.cell(row=row_num, column=23, value=tw2)
        ws.cell(row=row_num, column=24, value=tw3)
        ws.cell(row=row_num, column=25, value=tw4)

        # get cascading
        data_cascading = item.cascading
        if data_cascading:
            data = WorkingUnit.objects.filter(code__in=data_cascading).values_list("name", flat=True)
            cascading_nama = ", ".join(data)
        else:
            cascading_nama = None
        ws.cell(row=row_num, column=26, value=cascading_nama)

        center_columns = [1, 3, 8, 10, 11, 12, 13, 14, 16, 17, 18, 19, 21, 22, 23, 24, 25]
        
        for col in range(1, 27):
            cell = ws.cell(row=row_num, column=col)
            cell.font = normal_font
            cell.alignment = center if col in center_columns else left
            cell.border = border

        row_num += 1

    for col in range(1, ws.max_column + 1):
        header_1 = ws.cell(row=5, column=col).value
        header_2 = ws.cell(row=6, column=col).value

        max_length = max(
            len(str(header_1 or '')),
            len(str(header_2 or ''))
        )

        column_letter = get_column_letter(col)

        ws.column_dimensions[column_letter].width = max_length + 5

    excel_file = BytesIO()
    workbook.save(excel_file)
    excel_file.seek(0)

    return excel_file

def render_template(template_path, context=None):
    doc = DocxTemplate(template_path)
    if context:
        doc.render(context)

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return Document(buffer)

def export_file_rincian_target(unker_id, year, unker_nama):
    rows = []

    indicator = PerformanceIndicators.objects.filter(unker__id__in=unker_id, is_delete=False, year=year).order_by('unker_id__level', 'unker_id__code')

    for ik_idx, ik in enumerate(indicator, start=1):
        data_target = AchievementTarget.objects.filter(
            indicator=ik, category="Performance Indicator"
        ).first()

        if not data_target:
            row_num += 1
            continue

        tw1 = data_target.tw1 if data_target.tw1 else '-'
        tw2 = data_target.tw2 if data_target.tw2 else '-'
        tw3 = data_target.tw3 if data_target.tw3 else '-'
        tw4 = data_target.tw4 if data_target.tw4 else '-'

        rows.append({
            "no": ik_idx,
            "indikator": ik.title,
            "satuan": ik.unit,
            "periode": ik.period,
            "pola_perhitungan": ik.calculation_data,
            "tw1": tw1,
            "tw2": tw2,
            "tw3": tw3,
            "tw4": tw4,
        })

    context = {
        "rows": rows
    }

    doc_b = render_template(f"{settings.BASE_DIR}/static/rincian_target.docx", context)

    output = BytesIO()
    doc_b.save(output)
    output.seek(0)

    return output

def _build_rows_penetapan_ik(unker, year, template_doc):
    rows = []

    targets = (
        PerformanceTargets.objects.filter(
            working_unit=unker,
            is_delete=False,
            year=year
        ).prefetch_related("performanceindicators_set")
    )

    no_sasaran = 1
    formula_map = {}

    for target in targets:
        indicators = target.performanceindicators_set.filter(is_delete=False, unker=unker, year=year).order_by('created_at')

        if not indicators.exists():
            rows.append({
                "no_sasaran": no_sasaran,
                "sasaran": target.title,
                "no_ik": "",
                "indikator": "",
                "formula": "",
                "formula_detail": "",
                "penanggung_jawab": "",
            })

            no_sasaran += 1
            continue

        for i, indicator in enumerate(indicators):
            calculation_method_data = (
                indicator.calculation_method
                if indicator.calculation_method
                else None
            )
            calculation_method_detail_data = (
                indicator.calculation_method_detail
                if indicator.calculation_method_detail
                else None
            )

            formula = f"{calculation_method_data}\n\n\n{calculation_method_detail_data}"
            rows.append({
                "no_sasaran": no_sasaran if i == 0 else "",
                "sasaran": target.title if i == 0 else "",
                "no_ik": i + 1,
                "indikator": indicator.title,
                "formula": formula,
                "penanggung_jawab": indicator.unker.name,
            })

        no_sasaran += 1

    return rows, formula_map

def create_ttd_penetapan_indikator(tahun, unker):
    doc = Document()
    for _ in range(5):
        doc.add_paragraph()

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT

    # get pejabat berwenang
    pejabat = unker.title_set.first().officer.name if unker.title_set.first().officer.name else '-'

    run = p.add_run(
        f"........., .................... {tahun}\n\n"
        "........................................\n"
        "........................................\n\n"
        f"{pejabat}"
    )

    run.font.size = Pt(11)
    return doc

def export_file_penetapan_indikator(unker_id, year, unker_nama):
    unkers = WorkingUnit.objects.filter(
        id__in=unker_id,
        is_delete=False
    ).order_by("level", "code")

    if not unkers.exists():
        return None

    judul_sasaran = ""
    composer = None
    last_unker = None

    template_path = (
        f"{settings.BASE_DIR}"
        "/static/penetapan_indikator_kinerja.docx"
    )

    for unker in unkers:
        doc = DocxTemplate(template_path)

        rows, formula_map = _build_rows_penetapan_ik(
            unker,
            year,
            template_doc=doc
        )

        context = {
            "unker": unker.name.upper(),
            "tahun": year,
            "judul_sasaran": judul_sasaran,
            "rows": rows,
        }

        doc.render(context)

        if composer is None:
            composer = Composer(doc)
        else:
            if unker.level > 1:
                composer.doc.add_page_break()

            composer.append(doc)

        last_unker = unker

    if composer is None:
        return None

    if last_unker:
        ttd_doc = create_ttd_penetapan_indikator(
            year,
            last_unker
        )

        if ttd_doc:
            composer.append(ttd_doc)

    output = BytesIO()
    composer.save(output)
    output.seek(0)

    return output

def generate_capaian_indikator(unker_id, year, tw, unker_nama):
    if not unker_id:
        raise NotFound(detail="Unit Kerja not found")

    parent = WorkingUnit.objects.get(id=unker_id, is_delete=False)

    child = WorkingUnit.objects.filter(parent=parent, is_delete=False)

    indicators = PerformanceIndicators.objects.filter(
        is_delete=False,
        year=year,
        is_priority=True,
        unker__code__in=[parent, *child]
    ).select_related(
        'performance_targets',
        'performance_targets__working_unit',
        'unker'
    ).order_by(
        'performance_targets__working_unit__level',
        'performance_targets__working_unit__code',
        'unker__level',
        'unker__code',
        'created_at'
    )

    if tw:
        tw = tw
    else:
        now = datetime.now()
        month = MONTHS[now.month - 1]
        if month:
            for tw, daftar_bulan in PERIODE_MONTHS.items():
                if month in daftar_bulan:
                    tw = tw
            if tw is None:
                raise ValueError("TW NOT FOUND")
        
    wb = Workbook()
    ws = wb.active
    ws.title = 'Sheet1'

    header_fill = PatternFill(
        fill_type='solid',
        fgColor='4472C4'
    )

    target_fill = PatternFill(
        fill_type='solid',
        fgColor='FFFF00'
    )

    header_font = Font(
        bold=True,
        color='FFFFFF',
        size=10
    )

    target_font = Font(
        bold=True,
        color='000000',
        size=10
    )

    normal_font = Font(size=10)

    center = Alignment(
        horizontal='center',
        vertical='center',
        wrap_text=True
    )

    left = Alignment(
        horizontal='left',
        vertical='top',
        wrap_text=True
    )

    thin = Side(
        style='thin',
        color='000000'
    )

    border = Border(
        left=thin,
        right=thin,
        top=thin,
        bottom=thin
    )

    headers = [
        'No', # 1
        'Indikator', # 2
        'Satuan', # 3
        'Target', # 4
        f'Realisasi {tw.upper()}', # 5
        f'% Capaian {tw.upper()}', # 6
        'Faktor Pendukung', # 7
        'Faktor Penghambat', # 8
        'Upaya Tindak Lanjut', # 9
        'Penanggung Jawab', # 10
        'Cascading Indikator', # 11
        'Keterangan Data Capaian' # 12
    ]

    for col, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = center
        cell.border = border

    ws.row_dimensions[1].height = 35

    row_num = 2
    indicator_no = 1

    grouped_indicators = defaultdict(list)

    for indicator in indicators:
        if indicator.performance_targets:
            grouped_indicators[indicator.performance_targets].append(indicator)

    for col, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = center
        cell.border = border

    row_num = 2
    indicator_no = 1

    for performance_target, target_indicators in grouped_indicators.items():

        # Baris sasaran (warna kuning)
        ws.merge_cells(
            start_row=row_num,
            start_column=1,
            end_row=row_num,
            end_column=10
        )

        cell = ws.cell(
            row=row_num,
            column=1,
            value=performance_target.title
        )

        # styling sasaran
        for col in range(1, 13):
            cell = ws.cell(row=row_num, column=col)
            cell.fill = target_fill
            cell.font = target_font
            cell.border = border
            cell.alignment = left

        row_num += 1

        # Baris indikator
        for indicator in target_indicators:
            realisasi = 0
            persen = 0

            achievement_target = indicator.indicator_achievement.filter(category='Achievement Measurement', year=year).first()
            if achievement_target:
                realisasi = getattr(achievement_target, tw, 0)
                if realisasi is None:
                    realisasi = 0

            try:
                target_value = float(indicator.target or 0)
            except (ValueError, TypeError):
                target_value = 0

            persen = (
                (realisasi / target_value) * 100
                if target_value else 0
            )

            performance_measurement = indicator.performancemeasurement_set.filter(periode=tw).first()
            if performance_measurement:
                solution = performance_measurement.solution if performance_measurement.solution else ''
                obstacle = performance_measurement.obstacle if performance_measurement.obstacle else ''
                notes = performance_measurement.notes if performance_measurement.notes else ''

            ws.cell(row=row_num, column=1, value=indicator_no)
            ws.cell(row=row_num, column=2, value=indicator.title)
            ws.cell(row=row_num, column=3, value=indicator.unit)
            ws.cell(row=row_num, column=4, value=target_value)
            ws.cell(row=row_num, column=5, value=realisasi)
            ws.cell(row=row_num, column=6, value=persen)
            ws.cell(row=row_num, column=7, value=solution)
            ws.cell(row=row_num, column=8, value=obstacle)
            ws.cell(row=row_num, column=9, value='-')
            ws.cell(
                row=row_num,
                column=10,
                value=indicator.unker.name if indicator.unker else '-'
            )

            # Cascading
            data_cascading = indicator.cascading

            if data_cascading:
                data = WorkingUnit.objects.filter(
                    code__in=data_cascading
                ).values_list(
                    "name",
                    flat=True
                )

                cascading_nama = ", ".join(data)
            else:
                cascading_nama = ''

            ws.cell(
                row=row_num,
                column=11,
                value=cascading_nama
            )

            ws.cell(row=row_num, column=12, value=notes)

            # Styling indikator
            center_columns = [1, 3, 4, 5, 6, 9]

            for col in range(1, 13):
                cell = ws.cell(row=row_num, column=col)
                cell.font = normal_font
                cell.alignment = center if col in center_columns else left
                cell.border = border

            indicator_no += 1
            row_num += 1

    for col in range(1, ws.max_column + 1):
        header = ws.cell(row=1, column=col).value

        max_length = len(str(header or ''))

        column_letter = get_column_letter(col)

        ws.column_dimensions[column_letter].width = max_length + 8
    
    excel_file = BytesIO()
    wb.save(excel_file)
    excel_file.seek(0)

    return excel_file

def export_dokumen_kinerja(unker_id, year):
    data_unker = WorkingUnit.objects.filter(is_delete=False)
    
    data_dokumen = PerformanceDocument.objects.none()
    
    if unker_id:
        parent = data_unker.get(id=unker_id)
        child = data_unker.filter(parent=parent)

        data_dokumen = PerformanceDocument.objects.filter(unker__in=[parent, *child], is_delete=False, year=year).values(
            'unker__code',
        ).annotate(
            pohon_kinerja=Count('id', filter=Q(category='Pohon Kinerja')),
            renstrai=Count('id', filter=Q(category='Renstra')),
            renja=Count('id', filter=Q(category='Renja')),
            pk=Count('id', filter=Q(category='PK')),
            sk_indikator_kinerja=Count('id', filter=Q(category='SK Indikator Kinerja')),
            manual_indikator_kinerja=Count('id', filter=Q(category='Manual Indikator Kinerja')),
            matrix_cascading_mph=Count('id', filter=Q(category='Matrix Cascading / MPH')),
            rencana_aksi=Count('id', filter=Q(category='Rencana Aksi')),
            rincian_target_indikator=Count('id', filter=Q(category='Rincian Target Indikator')),
            laporan_kinerja_tw1=Count('id', filter=Q(category='Laporan Kinerja TW I')),
            laporan_kinerja_tw2=Count('id', filter=Q(category='Laporan Kinerja TW II')),
            laporan_kinerja_tw3=Count('id', filter=Q(category='Laporan Kinerja TW III')),
            laporan_kinerja_tw4=Count('id', filter=Q(category='Laporan Kinerja TW IV')),
            evaluasi_kinerja_tw1=Count('id', filter=Q(category='Evaluasi Kinerja TW I')),
            evaluasi_kinerja_tw2=Count('id', filter=Q(category='Evaluasi Kinerja TW II')),
            evaluasi_kinerja_tw3=Count('id', filter=Q(category='Evaluasi Kinerja TW III')),
            evaluasi_kinerja_tw4=Count('id', filter=Q(category='Evaluasi Kinerja TW IV')),
        )

    doc_map = {
        item["unker__code"]: item
        for item in data_dokumen
    }
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Sheet1"

    bold_font = Font(bold=True, size=10)
    
    center = Alignment(
        horizontal='center',
        vertical='center',
        wrap_text=True
    )

    left = Alignment(
        horizontal='left',
        vertical='top',
        wrap_text=True
    )

    normal_font = Font(size=10)

    thin = Side(
        style='thin',
        color='000000'
    )

    border = Border(
        left=thin,
        right=thin,
        top=thin,
        bottom=thin
    )

    ws.merge_cells('A2:A3')
    ws.merge_cells('B2:B3')
    ws.merge_cells('C2:C3')
    ws.merge_cells('D2:D3')

    ws.merge_cells('E2:U2')

    ws['A2'] = 'NO'
    ws['B2'] = 'LEVEL'
    ws['C2'] = 'KODE'
    ws['D2'] = 'UNIT KERJA'
    ws['E2'] = 'DOKUMEN KINERJA'

    headers = [
        'Pohon Kinerja',
        'Renstra',
        'Renja',
        'PK',
        'SK Indikator Kinerja',
        'Manual Indikator Kinerja',
        'Matriks Cascading / MPH',
        'Rencana Aksi',
        'Rincian Target Indikator',
        'Laporan Kinerja TW I',
        'Laporan Kinerja TW II',
        'Laporan Kinerja TW III',
        'Laporan Kinerja TW IV',
        'Evaluasi Kinerja TW I',
        'Evaluasi Kinerja TW II',
        'Evaluasi Kinerja TW III',
        'Evaluasi Kinerja TW IV',
    ]

    for idx, header in enumerate(headers, start=5):
        ws.cell(row=3, column=idx, value=header)

    for row in ws.iter_rows(min_row=2, max_row=3, min_col=1, max_col=21):
        for cell in row:
            cell.font = bold_font
            cell.alignment = center
            cell.border = border

    row_num = 4

    for no, unker in enumerate(data_unker.order_by('code'), start=1):
        item = doc_map.get(unker.code, {})

        ws.cell(row=row_num, column=1, value=no)
        ws.cell(row=row_num, column=2, value=unker.level)
        ws.cell(row=row_num, column=3, value=unker.code)
        ws.cell(row=row_num, column=4, value=unker.name)

        ws.cell(row=row_num, column=5, value=item.get("pohon_kinerja", 0))
        ws.cell(row=row_num, column=6, value=item.get("renstra", 0))
        ws.cell(row=row_num, column=7, value=item.get("renja", 0))
        ws.cell(row=row_num, column=8, value=item.get("pk", 0))
        ws.cell(row=row_num, column=9, value=item.get("sk_indikator_kinerja", 0))
        ws.cell(row=row_num, column=10, value=item.get("manual_indikator_kinerja", 0))
        ws.cell(row=row_num, column=11, value=item.get("matrix_cascading_mph", 0))
        ws.cell(row=row_num, column=12, value=item.get("rencana_aksi", 0))
        ws.cell(row=row_num, column=13, value=item.get("rincian_target_indikator", 0))
        ws.cell(row=row_num, column=14, value=item.get("laporan_kinerja_tw1", 0))
        ws.cell(row=row_num, column=15, value=item.get("laporan_kinerja_tw2", 0))
        ws.cell(row=row_num, column=16, value=item.get("laporan_kinerja_tw3", 0))
        ws.cell(row=row_num, column=17, value=item.get("laporan_kinerja_tw4", 0))
        ws.cell(row=row_num, column=18, value=item.get("evaluasi_kinerja_tw1", 0))
        ws.cell(row=row_num, column=19, value=item.get("evaluasi_kinerja_tw2", 0))
        ws.cell(row=row_num, column=20, value=item.get("evaluasi_kinerja_tw3", 0))
        ws.cell(row=row_num, column=21, value=item.get("evaluasi_kinerja_tw4", 0))

        center_columns = [1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21]
        
        for col in range(1, 22):
            cell = ws.cell(row=row_num, column=col)
            cell.font = normal_font
            cell.alignment = center if col in center_columns else left
            cell.border = border
        row_num += 1

    for col in range(1, ws.max_column + 1):
        header_1 = ws.cell(row=2, column=col).value
        header_2 = ws.cell(row=3, column=col).value

        max_length = max(
            len(str(header_1 or '')),
            len(str(header_2 or ''))
        )

        column_letter = get_column_letter(col)

        ws.column_dimensions[column_letter].width = max_length + 5

    virtual_workbook = BytesIO()
    wb.save(virtual_workbook)
    virtual_workbook.seek(0)
    return virtual_workbook