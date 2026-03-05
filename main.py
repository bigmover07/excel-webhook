from fastapi import FastAPI, Response
from pydantic import BaseModel
import pandas as pd
import io

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
    
    buffer.seek(0)
    
    headers = {
        'Content-Disposition': f'attachment; filename="compliance_report_{data.operator_name}.xlsx"'
    }
    return Response(content=buffer.getvalue(), 
                    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                    headers=headers)
