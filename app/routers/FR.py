from fastapi import FastAPI, Request, Form, APIRouter, Header, Response
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi import File, UploadFile
from app.library.helpers import *
from io import StringIO
from datetime import datetime
from typing import List

router = APIRouter()
templates = Jinja2Templates(directory="templates/")


@router.get("/uploadfilefr", response_class=HTMLResponse)
def get_upload(request: Request):
    result = "Excel file upload (csv, tsv, csvz, tsvz only)"
    return templates.TemplateResponse('FR.html', context={'request': request, 'result': result})


@router.post("/uploadfilefr/new/")
async def predict(request: Request, response: Response, fallFile: UploadFile = File(...), dbFile: UploadFile = File(...)):
    fall_content = await fallFile.read()
    db_content = await dbFile.read()
    fall_data = pd.read_excel(fall_content)
    db_data = pd.read_excel(db_content)
    res = predict_fr(db_data, fall_data)
    filename = 'fallback_reduction'
    # response.headers["filename"] = filename
    date = datetime.now().strftime("%Y_%m_%d_%I%M%S_%p")
    # ext = os.path.splitext(file.filename)[1]
    key = "FR" + "/" + filename + "_" + date + '.csv'
    excel_buffer = StringIO()
    res.to_csv(excel_buffer)
    s3_resource = boto3.resource('s3', aws_secret_access_key=AWS_SECRET_ACCESS_KEY, aws_access_key_id=AWS_ACCESS_KEY_ID)
    s3_resource.Object(AWS_S3_BUCKET, key).put(Body=excel_buffer.getvalue())
    # upload_file("D:/deepak files/codes_IECO/ieco_test_nqr.xls", AWS_S3_BUCKET)
    # res.to_excel(f"s3://{AWS_S3_BUCKET}/{key}", header=True, index=False, storage_options={
    #     "key": AWS_ACCESS_KEY_ID,
    #     "secret": AWS_SECRET_ACCESS_KEY})
    # print(context["X-Request-ID"])
    object_name = get_object_name(AWS_S3_BUCKET, PREFIX_FR)
    creds = create_presigned_url(AWS_S3_BUCKET, object_name)
    # print(creds)
    return templates.TemplateResponse('FR.html', context={'request': request, 'creds': creds, 'result': res,
                                                           'tables': [res.to_html()],
                                                           'titles': res.columns.values},
                                      headers={'filename': filename})


@router.get("/uploadfilefr/new/download")
def download(request: Request):
    object_name = get_object_name(AWS_S3_BUCKET, PREFIX_FR)
    response = create_presigned_post(AWS_S3_BUCKET, object_name)
    url = response['url']
    filename = os.path.basename(response['fields']['key'])
    path = url + response['fields']['key']
    return FileResponse(path=path, media_type='text/csv',
                        headers={"Content-Disposition": f"attachment;filename={filename}"})
