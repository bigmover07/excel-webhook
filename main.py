from fastapi import FastAPI, Response
from pydantic import BaseModel
import pandas as pd
import io
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill

app = FastAPI()

# Define the expected incoming data structure
class ReportData(BaseModel):
    operator_name: str
    assets: list[dict] 

@app.post("/report/xlsx")
async def generate_excel_report(data: ReportData):
    df = pd.DataFrame(data.assets)
    buffer = io.BytesIO()
    
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Compliance Report', index=False)
        
        # Access the raw workbook and worksheet factory
        workbook = writer.book
        worksheet = writer.sheets['Compliance Report']
        
        # 1. Define our visual aesthetics
        thin_border = Border(
            left=Side(style='thin'), right=Side(style='thin'), 
            top=Side(style='thin'), bottom=Side(style='thin')
        )
        center_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        bold_font = Font(bold=True)
        
        # 2. Define the "Extreme Urgency" styling (Light red background, dark red text)
        red_fill = PatternFill(start_color='FFC7CE', end_color='FFC7CE', fill_type='solid')
        red_font = Font(color='9C0006', bold=True)
        
        # 3. Find exactly which column holds the "Urgency" data
        urgency_col_idx = None
        for col_idx, col_name in enumerate(df.columns):
            if col_name == "Urgency":
                urgency_col_idx = col_idx + 1 # OpenPyXL uses 1-based indexing
                break

        # 4. Apply all styles cell-by-cell
        for row_idx, row in enumerate(worksheet.iter_rows()):
            
            # Check if this specific row is marked "Critical"
            is_critical = False
            if row_idx > 0 and urgency_col_idx:
                urgency_val = row[urgency_col_idx - 1].value
                if urgency_val == "Critical":
                    is_critical = True

            for cell in row:
                cell.border = thin_border
                cell.alignment = center_alignment
                
                # If it's the very first row, bold the headers
                if row_idx == 0: 
                    cell.font = bold_font
                else: 
                    # If it's a data row AND it's critical, turn it red
                    if is_critical:
                        cell.fill = red_fill
                        cell.font = red_font
                        
        # 5. Auto-adjust column widths so nothing is cut off
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            worksheet.column_dimensions[column_letter].width = (max_length + 3)

    buffer.seek(0)
    
    headers = {
        'Content-Disposition': f'attachment; filename="compliance_report_{data.operator_name}.xlsx"'
    }
    return Response(
        content=buffer.getvalue(), 
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
        headers=headers
    )
