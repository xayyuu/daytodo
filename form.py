# -*- coding: UTF-8 -*-
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Length


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(1, 60)])
    password = PasswordField("Password", validators=[DataRequired(), Length(4, 20)])
    submitbtn = SubmitField("Login")

#
#
# class TodoListForm(FlaskForm):
#     title = StringField('标题', validators=[DataRequired(), Length(1, 64)])
#     status = RadioField('是否完成', validators=[DataRequired()], choices=[("1", '是'), ("0", '否')])
#     submit = SubmitField('提交')
#
#
