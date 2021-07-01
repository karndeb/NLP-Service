from fastapi import FastAPI, Request, Form, APIRouter
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi import File, UploadFile
from app.library.helpers import *
from io import StringIO
from datetime import datetime

router = APIRouter()
templates = Jinja2Templates(directory="templates/")


@router.get("/uploadfileqe", response_class=HTMLResponse)
def get_upload(request: Request):
    result = "Excel file upload (csv, tsv, csvz, tsvz only)"
    return templates.TemplateResponse('QE.html', context={'request': request, 'result': result})


@router.post("/uploadfileqe/new/")
async def post_upload(request: Request, file: UploadFile = File(...)):
    content = await file.read()
    data = pd.read_excel(content)
    res = predict_qe(data)
    filename = os.path.splitext(file.filename)[0]
    # response.headers["filename"] = filename
    date = datetime.now().strftime("%Y_%m_%d_%I%M%S_%p")
    # ext = os.path.splitext(file.filename)[1]
    key = "QE" + "/" + filename + "_" + date + '.csv'
    excel_buffer = StringIO()
    res.to_csv(excel_buffer)
    s3_resource = boto3.resource('s3', aws_secret_access_key=AWS_SECRET_ACCESS_KEY, aws_access_key_id=AWS_ACCESS_KEY_ID)
    s3_resource.Object(AWS_S3_BUCKET, key).put(Body=excel_buffer.getvalue())
    object_name = get_object_name(AWS_S3_BUCKET, PREFIX_QE)
    creds = create_presigned_url(AWS_S3_BUCKET, object_name)
    # print(creds)
    return templates.TemplateResponse('QE.html', context={'request': request, 'creds': creds, 'result': res,
                                                           'tables': [res.to_html()],
                                                           'titles': res.columns.values},
                                      headers={'filename': filename})


@router.get("/uploadfileqe/new/download")
def download(request: Request):
    object_name = get_object_name(AWS_S3_BUCKET, PREFIX_QE)
    response = create_presigned_post(AWS_S3_BUCKET, object_name)
    url = response['url']
    filename = os.path.basename(response['fields']['key'])
    path = url + response['fields']['key']
    return FileResponse(path=path, media_type='text/csv',
                        headers={"Content-Disposition": f"attachment;filename={filename}"})