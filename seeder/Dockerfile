FROM python:3.7-slim
ADD . /seeder
WORKDIR /seeder
RUN pip install -r requirements.txt
CMD ["/seeder/seeder.py"]
ENTRYPOINT ["python"]