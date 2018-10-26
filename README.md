# daytodo
demo for todolist, use flask framework to release.


# 手动生成admin账号的方法

目前还没有实现自动添加用户的功能，所以需要操作数据库文件来实现添加数据。
步骤：
1. python app.py shell
2. user_a = User("somebody", "password")
3. db.session.add(user_a)
4. db.session.commit()

如此，则在data.sqlite中添加了一条新的user记录。
> data.sqlite 是在创建迁移仓库之后，使用upgrade命令生成。
使用数据库迁移库，可跟踪数据库的变化，比如表结构的修改，增删表等等。

