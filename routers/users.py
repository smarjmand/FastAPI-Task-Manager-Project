import sys
from .tools import *
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette import status
from starlette.responses import RedirectResponse
from pydantic import BaseModel
from passlib.context import CryptContext
sys.path.append(...)


router = APIRouter(
    prefix='/user',
    tags=['Users']
)

template = Jinja2Templates(directory='templates')
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


#--------------------------------------------------------------------------------------------------------
# to change current password :
@router.get('/edit-password', response_class=HTMLResponse)
async def edit_password(request: Request):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url='/auth', status_code=status.HTTP_302_FOUND)
    context = {'request': request, 'user': user}
    return template.TemplateResponse('edit-user-password.html', context)


@router.post('/edit-password', response_class=HTMLResponse)
async def user_password_change(
        request: Request, db: db_dependency, username: str = Form(...),
        password: str = Form(...), new_password: str = Form(...)
):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url='/auth', status_code=status.HTTP_302_FOUND)

    user_data: Users = db.query(Users).filter(Users.username == username).first()
    msg = 'Invalid username or password'

    if user_data is not None:
        if username == user_data.username and bcrypt_context.verify(password, user_data.hashed_password):
            user_data.hashed_password = bcrypt_context.hash(new_password)
            db.add(user_data)
            db.commit()
            msg = 'Password updated'

    context = {'request': request, 'msg': msg, 'user': user}
    return template.TemplateResponse('edit-user-password.html', context)
