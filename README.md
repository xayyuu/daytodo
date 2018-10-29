# daytodo
demo for todolist, use flask framework to release.

# 运行方法  
- 创建虚拟环境；
- 使用pip 安装requirements.txt里的依赖包；
```buildoutcfg
pip install -r requirements.txt
```
- 进入代码目录，执行命令：
```buildoutcfg
python app.py runserver
```

# 手动生成admin账号的方法

目前已实现自动添加账号的界面，但有时候若需要手动操作，可参考下列步骤：
1. python app.py shell
2. user_a = User("somebody", "password")
3. db.session.add(user_a)
4. db.session.commit()

如此，则在data.sqlite中添加了一条新的user记录。
> data.sqlite 是在创建迁移仓库之后，使用upgrade命令生成。
使用数据库迁移库，可跟踪数据库的变化，比如表结构的修改，增删表等等。


# 每次修改orm类型时，需要手动迁移数据库
步骤：
```buildoutcfg
 python app.py db migrate -m  "some comment"
 python app.py db upgrade
```

如果迁移出错，可以考虑删除之前的迁移仓库（先备份），并重新执行：
```buildoutcfg
python app.py db init 
python app.py db migrate -m "init"
python app.py db upgrade 
```

# 环境变量   

因为需要使用邮件功能，所以需要设置下列环境变量： 
```buildoutcfg
export MAIL_USERNAME="kidult1107@126.com"
export MAIL_PASSWORD="yutianyou1107"
#export TODOLIST_ADMIN="kidult1107@126.com" 
export FLASKY_ADMIN="kidult1107@126.com" 
```

# 常见问题

- 确认失败，需要检查收件邮箱是否拒收了该邮件，或者把邮件自动移到了垃圾邮件


