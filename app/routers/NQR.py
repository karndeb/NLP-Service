from fastapi import FastAPI, Request, Form, APIRouter, Header, Response
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi import File, UploadFile
from app.library.helpers import *
from io import StringIO
from datetime import datetime
from typing import List, Optional
import requests
from starlette_context import context

router = APIRouter()
templates = Jinja2Templates(directory="templates/")


@router.get("/uploadfile", response_class=HTMLResponse)
def get_upload(request: Request):
    result = "Excel file upload (csv, tsv, csvz, tsvz only)"
    return templates.TemplateResponse('NQR.html', context={'request': request, 'result': result})


# @router.post("/uploadfile/new/")
# def save_upload_file_tmp(file: UploadFile) -> Path:
#     try:
#         suffix = Path(file.filename).suffix
#         with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
#             shutil.copyfileobj(file.file, tmp)
#             tmp_path = Path(tmp.name)
#     finally:
#         file.file.close()
#     return tmp_path


# @router.post("/uploadfile/new/")
# async def predict(request: Request, max_sentences: int = Form(...), file: UploadFile = File(...)):
#     content = await file.read()
#     data = pd.read_excel(content)
#     res = predict_nqr(data, max_sentences)
#     res.to_excel(file_path + file.filename, index=False, header=True)
#     return templates.TemplateResponse('NQR.html', context={'request': request, 'result': res, 'tables': [res.to_html()],
#                                                            'titles': res.columns.values})


@router.post("/uploadfile/new/")
async def predict(request: Request, response: Response, max_sentences: int = Form(...), file: UploadFile = File(...)):
    content = await file.read()
    data = pd.read_excel(content)
    res = predict_nqr(data, max_sentences)
    filename = os.path.splitext(file.filename)[0]
    # response.headers["filename"] = filename
    date = datetime.now().strftime("%Y_%m_%d_%I%M%S_%p")
    # ext = os.path.splitext(file.filename)[1]
    key = "NQR" + "/" + filename + "_" + date + '.csv'
    excel_buffer = StringIO()
    res.to_csv(excel_buffer)
    s3_resource = boto3.resource('s3', aws_secret_access_key=AWS_SECRET_ACCESS_KEY, aws_access_key_id=AWS_ACCESS_KEY_ID)
    s3_resource.Object(AWS_S3_BUCKET, key).put(Body=excel_buffer.getvalue())
    # upload_file("D:/deepak files/codes_IECO/ieco_test_nqr.xls", AWS_S3_BUCKET)
    # res.to_excel(f"s3://{AWS_S3_BUCKET}/{key}", header=True, index=False, storage_options={
    #     "key": AWS_ACCESS_KEY_ID,
    #     "secret": AWS_SECRET_ACCESS_KEY})
    # print(context["X-Request-ID"])
    object_name = get_object_name(AWS_S3_BUCKET, PREFIX_NQR)
    creds = create_presigned_url(AWS_S3_BUCKET, object_name)
    # print(creds)
    return templates.TemplateResponse('NQR.html', context={'request': request, 'creds': creds, 'result': res,
                                                           'tables': [res.to_html()],
                                                           'titles': res.columns.values},
                                      headers={'filename': filename})


# @router.get("/uploadfile/new/signed_url")
# async def get_filename(filename: Optional[List[str]] = Header(None)):
#     return {"filename": filename}


@router.get("/uploadfile/new/download")
def download(request: Request):
    # s3_client = boto3.client('s3', aws_secret_access_key=AWS_SECRET_ACCESS_KEY, aws_access_key_id=AWS_ACCESS_KEY_ID)
    object_name = get_object_name(AWS_S3_BUCKET, PREFIX_NQR)
    response = create_presigned_post(AWS_S3_BUCKET, object_name)
    url = response['url']
    filename = os.path.basename(response['fields']['key'])
    # file = s3_client.get_object(Bucket=AWS_S3_BUCKET, Key=filename)
    path = url + response['fields']['key']
    # download_url = create_presigned_url(AWS_S3_BUCKET, object_name)
    # file_like = open(path, mode='rb')
    # r = requests.get(url, allow_redirects=True)
    # open(f"{filename}", 'wb').write(r.content)
    # download_file(AWS_S3_BUCKET, PREFIX_NQR)
    # response['headers'] = {'Content-Disposition": "attachment;filename=f"{filename}"'}
    return FileResponse(path=path, media_type='text/csv',
                        headers={"Content-Disposition": f"attachment;filename={filename}"})
    # return StreamingResponse(file_like, media_type='application/octet-stream',
    #                          headers={"Content-Disposition": f"attachment;filename={filename}"})



