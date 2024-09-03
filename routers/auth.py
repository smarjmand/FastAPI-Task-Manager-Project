import sys
from fastapi import APIRouter, Response, Form
from fastapi.security import OAuth2PasswordRequestForm
from .tools import *
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from typing import Optional, Union
sys.path.append("..")

router = APIRouter(
    prefix='/auth',
    tags=['Authentication']
)


class LoginForm():
    def __init__(self, request: Request):
        self.request: Request = request
        self.username: Optional[str] = None
        self.password: Optional[str] = None

    async def create_oauth_form(self):
        form = await self.request.form()
        self.username = form.get("email")
        self.password = form.get("password")


templates = Jinja2Templates(directory='templates')


#--------------------------------------------------------------------------------------------------------
# to create token for user :
@router.post("/token")
async def login_for_access_token(
        response: Response,
        # form_data: OAuth2PasswordRequestForm = Depends() ,
        form_data: Union[OAuth2PasswordRequestForm, LoginForm] = Depends(),
        db: Session = Depends(get_db)
):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        return False
    token_expires = timedelta(minutes=60)
    token = create_access_token(
        user.username, user.id, user.role, expires_delta=token_expires
    )

    response.set_cookie(key="access_token", value=token, httponly=True)

    return True


#--------------------------------------------------------------------------------------------------------
# to login user :
@router.get('/', response_class=HTMLResponse)
async def authentication_page(request: Request):
    return templates.TemplateResponse('login.html', {'request': request})


@router.post('/', response_class=HTMLResponse)
async def login(request: Request, db: db_dependency):
    try:
        form = LoginForm(request)
        await form.create_oauth_form()
        response = RedirectResponse(url='/todos', status_code=status.HTTP_302_FOUND)

        validate_user_cookie = await login_for_access_token(
            response=response, form_data=form, db=db
        )
        if not validate_user_cookie:
            context = {'request': request, 'msg': 'Incorrect Username or Password'}
            return templates.TemplateResponse('login.html', context)
        return response

    except HTTPException:
        context = {'request': request, 'msg': 'Unknown Error'}
        return templates.TemplateResponse('login.html', context)


#--------------------------------------------------------------------------------------------------------
# to logout user :
@router.get('/logout')
async def logout(request: Request):
    context = {'request': request, 'msg': 'Logout Successful'}
    response = templates.TemplateResponse('login.html', context)
    response.delete_cookie(key='access_token')
    return response


#--------------------------------------------------------------------------------------------------------
# to register new user :
@router.get('/register', response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse('register.html', {'request': request})


@router.post('/register', response_class=HTMLResponse)
async def register_user(
        db: db_dependency,
        request: Request, email: str = Form(...),
        username: str = Form(...), firstname: str = Form(...),
        lastname: str = Form(...), password: str = Form(...),
        password2: str = Form(...)
):
    validation1 = db.query(Users).filter(Users.username == username).first()
    validation2 = db.query(Users).filter(Users.email == email).first()

    if password != password2 or validation1 is not None or validation2 is not None:
        context = {'request': request, 'msg': 'Invalid registration request'}
        return templates.TemplateResponse('register.html', context)

    user_model = Users()
    user_model.username = username
    user_model.first_name = firstname
    user_model.last_name = lastname
    user_model.email = email
    user_model.hashed_password = bcrypt_context.hash(password)
    user_model.is_active = True

    db.add(user_model)
    db.commit()

    context = {'request': request, 'msg': 'User successfully created'}
    return templates.TemplateResponse('login.html', context)
