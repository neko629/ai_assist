# ai_assist


## 基础设置
### MySQL 安装
```SQL
sudo docker run -d --name mysql-ai-assist -p 3306:3306 -v $/home/neko/mysql/mysql_data_ai_assist:/var/lib/mysql -e MYSQL_ROOT_PASSWORD=000000 mysql:8.0
```

把依赖的包写入 `requirements.txt` 文件：
```bash
pip install pipreqs
pipreqs ./ --encoding=utf8 --force
```