build-image:
	cp Dockerfile.singleuser Dockerfile.datascience
	cp Dockerfile.singleuser Dockerfile.deeplearning
	cp Dockerfile.singleuser Dockerfile.nlp
	docker build -t wodeai/datascience:hubdev -f Dockerfile.datascience .
	docker build -t wodeai/deeplearning:hubdev -f Dockerfile.deeplearning .
	docker build -t wodeai/nlp:hubdev -f Dockerfile.nlp .

clear:
	-docker ps -a -q | xargs --no-run-if-empty  docker stop
	-docker ps -a -q | xargs  --no-run-if-empty docker rm 
	-docker images -q --filter "dangling=true" | xargs --no-run-if-empty  docker rmi
jhub:
	jupyterhub -f jupyterhub_config.py

dev: clear jhub	
