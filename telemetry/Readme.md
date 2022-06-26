# Build 
Build a new Prometheus image with your config:
```
docker build -t prometheus/cluster-local .

```

# Run Prometheus
You can now run Prometheus. If you need to tweak the config make sure you build the image between removing and running the container a second time.

```
docker run -p 9090:9090 --restart=always --name prometheus-rpi --net="host" -d prometheus/cluster-local
```

Note:
--net="host" is used to access an instance of nodeexporter running on localhost.


Was following https://blog.alexellis.io/prometheus-nodeexporter-rpi/
