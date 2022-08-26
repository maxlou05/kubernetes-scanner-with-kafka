# ncyd-nf-scanning
Scans Kubernetes cluster for changes in namespace, and matches the namespaces with defined network functions (in settings.json).

When change is detected, sends it to Kafka, which is also located on the cluster.

## Deployment
1. Deploying Kafka
    - `kubectl apply` the kafka `confluent_all_services.yml` manifest (will deploy all necessary services to `confluent` namespace)
2. Deploying the scanner app
    - Build an image using the provided Dockerfile
    - Change the image tag in the app `deploy.yml` manifest to the image that was just built
    - `kubectl apply` both the `role_settings.yml` and `deploy.yml`

## Visualization
Kowl can be used to visualize the data within the kafka cluster

(needs to be installed separately using helm)

1. Use the Kowl `kowl_values.yml` manifest to install Kowl with [helm](https://github.com/cloudhut/charts)
2. `kubectl port-forward` port 8080 (as instructed after the install)
