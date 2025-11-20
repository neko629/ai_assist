# ai_assist


## 基础设置
### MySQL 安装
```bash
sudo docker run -d --name mysql-ai-assist -p 3306:3306 -v /home/neko/mysql/mysql_data_ai_assist:/var/lib/mysql -e MYSQL_ROOT_PASSWORD=000000 mysql:8.0
```
### redis 安装
```bash
docker run -d --name redis-ai-assist -p 16379:6379 --restart always redis
 ```


把依赖的包写入 `requirements.txt` 文件：
```bash
pip install pipreqs
pipreqs ./ --encoding=utf8 --force
```