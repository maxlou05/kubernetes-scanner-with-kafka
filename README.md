# Network Function Namespace Scanner to Update Topology View
This Kubernetes app automatically scans the Kubernetes cluster periodically for namespaces that match with 5G network functions.
It then sends this information, as well as the changes compared with the previous scan, to a Kafka Topic.
From there, it will automatically be sent to Azure Log Analytics and update the CyberDome topology view.

## Deploying Kafka onto Kubernetes
1. `kubectl apply` the provided YAML manifest for Kafka (`manifests/Kafka/confluent_all_services.yml`) (it uses the Confluent Kafka platform; the images and manifests are provided by Confluent)

## Configuring scanner app
1. `kubectl apply` the role permissions manifest (`manifests/app/role_settings.yml`) because the app requires permissions to be able to scan the whole cluster’s namespaces
2. In the `settings.json` file:
    - `network_functions`: Contains all network functions that the scanner will be looking for. If the name of a namespace contains one of these network functions, it will be considered a network function
    - `scan_interval_minutes`: Delay time between each scan in minutes
    - `kafka_config.topic`: Name of the topic to post to
    - `kafka_config.api_ip`: IP of the kafka rest proxy, current default is the service pointing to Confluent Kafka REST proxy, if Confluent Kafka was deployed as mentioned in previous section
    - `debug`: `true` for more verbose outputs, default is `false` 


## Deploying the scanner app
1. Build an image using the provided `Dockerfile`
2. Update the app manifest (`manifests/app/deploy.yml`) to use the image that was just built
3. `kubectl apply` the app manifest to deploy the app

## Using Kowl to view data stored within Kafka
1. Install Kowl using [Helm](https://github.com/cloudhut/charts) or [Terraform](https://github.com/cloudhut/terraform-modules) (The Helm version is used in this project, the rest of the steps assume installation using Helm)
2. When installing, instead of using `values.yml`, use the provided manifest (`manifests/kowl/kowl_values.yml`)
    - The only difference is the brokers, put the Kafka server/broker IP there (currently uses Confluent’s provided service)
3. `kubectl port-forward` port 8080 (as instructed after the install)
4. Access to the Kowl UI is now available on the browser at `localhost:8080`
