# Candidate Project for Satispay
*Author: Piero Marraffa*
*codebase available in https://github.com/PieroMarraffa/Satispay_test_project*

## 1. Project Overview
**The Objective:** - Create a Terraform configuration that provisions a simple AWS architecture to persist and retrieve JSON data.

**Requirements:** 
1. **Infrastructure** (Terraform):
    - **Compute**: Provision an AWS Lambda function.
    - **Storage**: Provision an AWS DynamoDB table.
    - **Security**: Create the necessary IAM Roles and Policies. Follow the Principle of Least Privilege (e.g., the Lambda should only have permission to write/read from this specific DynamoDB table, not *).
    - **Logging**: Ensure the Lambda function outputs logs to AWS CloudWatch Logs.
2. **Application Logic** (Python/Node.js/Go - your choice):
    - **Ingestion**: The Lambda must accept a JSON payload (e.g., {"id": "123", "message": "hello"}) and persist it to the DynamoDB table.
    - **Retrieval**: Implement a way to retrieve the persisted data using its ID
    - **Architectural Decision**: You must decide whether to create a second Lambda for the retrieval step or reuse the existing one. Please document your reasoning in a README.

**Guidelines:** 
- **Keep it simple**: You do not need to build a full CI/CD pipeline or a complex API Gateway (unless you want to). Invoking the function via AWS Console or AWS CLI for testing is acceptable.
- **State Management**: Local state (terraform.tfstate) is acceptable for this exercise.
- **Clean Code**: Avoid hardcoding values (e.g., table names, region) in your code; use Terraform variables and outputs.

**Bonus Points:** 
- Use a **Makefile** or **shell script** to wrap the build/deploy commands.
- Include a basic **architectural diagram** in your README with any observations you might have.
- Feel free to **add any resource you think** would be useful.

___

## 2. Architectural Decisions

### Why two lambdas?

In the assignment I was asked to decide between one single lambda to manage API calls or divide the management between two of them. So I've gone for two for respecting the assignment of **least privilege**. Infact by doing this I could have **use two separate IAM roles** and assign to each lambda just the "allows" it needs.

### API Gateway

For reaching the lambdas, I've opted for **AWS API Gateway HTTP v2 version**. In fact, besides the fact that I've already used it in my previous projects, it was the **simplest and most efficient** way to implement the API requests. I've used proxy integration, CORS config and lambda implementation to configure the entire service.

### KMS integration

Speaking of security, I immediately thought of DynamoDB's **data-at-rest encryption**. I'd never used this service before, but I was familiar with its implementation, having studied it during my AWS certification preparation.

### Terraform state

Even if not mandatory, I've written the code for releasing an S3 for storing tf state of the project. I use it by default in the configuration scripts, but the infrastructure still works if manually released without the backend S3.

### UI and Automations

Even if not requested, I've implemented a react web app and multiple automation files just to make configuration, testing and destroying the infrastructure easier and more agile for interviewer. Since I wanted to focus on infrastructure design, implementation and testing, I've used AI tools to help me implement this features. Of course the infrastructure is still configurable and testable in manual ways that I'll explain in the relative chapter of this documentation.

___

## 3. Architecture Diagram and Flow

By using draw.io online tool I've realised the following architecture design schema. It's based on resources available in AWS Free Tier Account. 

![Cloud Design](cloud_architecture.jpg)

### Infrastructure Flow
1. **Client** send a CURL request to the API Gateway (if using UI for testing I've linked the Website endpoint to API GTW CORS configuration) 
2. Depending on the request, **API GTW** invoke the right lambda by using its lambda integration and permission
3. **Lambdas** access the DynamoDB tables with **IAM Role** restricted to the least possible privilege 
4. **DynamoDB** persist data and encrypt them at rest with **KMS Key**
5. Lambda functions and API Gateway log to **AWS CloudWatch Logs** in their dedicated Log Groups. (IAM Roles provide them the possibility to perform these actions)

___

## 4. Getting Started

### Prerequisites

- **AWS CLI** - [Installed](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) and configured (`aws configure --profile <profile_name>`) 
- **Terraform** - [Installed](https://developer.hashicorp.com/terraform/install) and inserted in path (follow this [doc](https://terraform-tutorial.schoolofdevops.com/00-environment-setup/))
- **Python 3** — just for setup/destroy scripts; [python.org](https://www.python.org/downloads/).
- **Node.js / npm** — just for UI release: [nodejs.org](https://nodejs.org/).

### Automatic Setup

This field is thought for making tester life easier. I've realized all the necessary scripts to deploy the infrastructure and destroy it after completing the tests.

**CRITICAL** - make it sure to respect all the prerequisites written above, otherwise the scripts will fail saying `Dependency not installed`

#### Mac users

Enter the repository of the project by using `cd` command 

1. Find the project directory in your "finder" 
2. Copy the whole path of the directory
3. Launch terminal app with cmd+space and type "terminal" (sudo role not necessary)
4. type:
    ```
    cd <directory path>
    ```

Make the scripts executable:
```
chmod +x macos_linux_scripts/first_configuration.sh
```

then run the configuration script:
```
./macos_linux_scripts/first_configuration.sh
```

To setup the whole project follow these steps:

`? Select AWS profile: (Use arrow keys)` 

Navigate with up/down arrow keys to the aws profile you want to use for deploying the infrastructure

`? Release UI site as well? (y/N)`

Type `y` to release the ui website

`? AWS region: eu-central-1`
`? Terraform state key: terraform.tfstate`

Press `Enter` on both to go on the configuration

Once finished on the installation you'll get 
`🌐 URL:`
in console. 
Follow the url to reach the testing website.

#### Windows users

Enter the repository of the project by using `cd` command 

1. Find the project directory in your "file explorer" 
2. Copy the whole path of the directory
3. Launch powershell app (admin role not necessary)
4. type:
    ```
    cd <directory path>
    ```

then run the configuration script:
```
.\windows_scripts\first_configuration.cmd
```

To setup the whole project follow these steps:

`? Select AWS profile: (Use arrow keys)` 

Navigate with up/down arrow keys to the aws profile you want to use for deploying the infrastructure

`? Release UI site as well? (y/N)`

Type `y` to release the ui website

`? AWS region: eu-central-1`
`? Terraform state key: terraform.tfstate`

Press `Enter` on both to go on the configuration

Once finished on the installation you'll get 
`🌐 URL:`
in console. 
Follow the url to reach the testing website.



### Manual Setup
**DISCLAIMER** - Manual setup is advised for users who prefer direct control over Terraform commands.

For setting up manually the infrastructure follow these steps:

1. Enter the repository of the project by using `cd` command 

    1. Find the project directory in your "file explorer" 
    2. Copy the whole path of the directory
    3. Launch powershell app (admin role not necessary)
    4. type:
        ```
        cd <directory path>
        ```
2. update the following commands with your desired aws profile and testing mode. I would advise to release the ui website (*test_via_ui=true*), but it's on your discretion, it won't change the test outcome.
For **mac users**:
    ```
    terraform -chdir=./cloud_infrastructure/infrastructure init -var="profile=<your AWS Profile>" -var="test_via_ui=<true/false>"
    ```
    For **windows users**:
    ```
    terraform -chdir=.\cloud_infrastructure\infrastructure init -var="profile=<your AWS Profile>" -var="test_via_ui=<true/false>"
    ```
3. Now let's apply the infrastructure:
For **mac users**:
    ```
    terraform -chdir=./cloud_infrastructure/infrastructure apply -auto-approve -var="profile=<your AWS Profile>" -var="test_via_ui=<true/false>"
    ```
    For **windows users**:
    ```
    terraform -chdir=.\cloud_infrastructure\infrastructure apply -auto-approve -var="profile=<your AWS Profile>" -var="test_via_ui=<true/false>"
    ```
4. In any moment you'll be able to run the command again and deploy or destroy the website. Remember to init the terraform (step 2) every time you'll modify *test_via_ui*
5. If *test_via_ui=true* web app build is needed. Follow this steps:
    a. Enter the website code subdirectory:
    ```
    cd cloud_infrastructure/infrastructure/s3_website/code
    ``` 
    b. Build the web app:
    ```
    npm i
    npm run build
    ``` 
    c. Upload the build files to the hosting s3 or manually or by the command:
    ```
    aws s3 sync dist/ s3://marraffa-satispay-site/ --delete --profile <AWS profile>
    ``` 

___

## 5. How to Test the Infrastructure
### UI Test

If released, you'll be able to reach the website by following the URL in:
`cloud_infrastructure/infrastructure/ui_website_url`

Here you'll find three different pages:
1. main page with all the created messages
2. by selecting one message you'll get to the detail page
3. by clicking to `+ New Message` you'll be able to create a new message

### CLI Test
At the end of the installation you'll find a new file at:
`cloud_infrastructure/infrastructure/s3_website/code/.env.local`

You'll be able to test them in terminal with the following commands
1. copy the whole text in `cloud_infrastructure/infrastructure/s3_website/code/.env.local`. It'll be something like `VITE_API_BASE_URL=...
`
2. send in terminal app the following command (works only on mac and linux. If on windows skip this step and change in every other commands VITE_API_BASE_URL with your actual api url):
    ```
    export VITE_API_BASE_URL=...
    ```
    paste here the text you copied before
3. for creating a new message use the following commands.
    In the given Application Logic the proposed json had the fields "id" and "message". In mine I left the id managed by lambda so I called it "title". Plus I considered the entire entity as a message so the second field turned into "text".

    <br>
    
    In macos/linux:
    ```
    curl -X POST "$VITE_API_BASE_URL/messages" -H "Content-Type: application/json" -d '{"title":"First meassage","text":"Hello world"}'
    ```
    In windows:
    ```
    Invoke-RestMethod -Uri "$VITE_API_BASE_URL/messages" `
    -Method Post `
    -Headers @{"Content-Type" = "application/json"} `
    -Body '{"title":"First meassage","text":"Hello world"}'
    ```
4. for listing all messages in mac/linux:
    ```
    curl "$VITE_API_BASE_URL/messages"
    ```
    in windows:
    ```
    Invoke-RestMethod -Uri "$VITE_API_BASE_URL/messages"
    ```
5. for reading a message by its id in mac/linux:
    ```
    curl "$VITE_API_BASE_URL/messages/<id>"
    ```
    in windows:
    ```
    Invoke-RestMethod -Uri "$VITE_API_BASE_URL/messages/<id>"
    ```
    you'll find the id from the list api response

___

## 6. Technical Implementation Details

### Project Structure

The project consists of 3 main directory
1. **cloud_infrastructure** - here is located the whole infrastructure comprehensive of terraform code, lambda code and react code. Everything here is going to the cloud;
2. **macos_linux_scripts** - here are located the scripts executable on Unix machines for configuring the infrastructure and destroying it;
3. **windows_scripts** - here are located the scripts executable on Windows machines for configuring the infrastructure and destroying it;

Speaking about **Terraform**, it's used in 3 different projects parts:
1. bootstrap infrastructure: here are created the resources for bootstrapping the project like the S3 that host the project terraform state;
2.  resources: here are created the resources linked to the solution designed, from the API Gateway to the IAM roles;
3. s3_website/terraform: here are created the resources to host the website like the S3 with website configuration;

Modules, tags and locals are terraform blocks largely used in the project to implement the recursive deploy of different resources with the same configuration.

### State Management
From the project instructions, management of the terraform state was very elastic:

*`Local state (terraform.tfstate) is acceptable for this exercise`*

Based on my past experiences where I got used to manage it with S3 buckets, I've provided an automated way to do it (bootstrap configuration) and a manual way to keep it local. The algorithm is based on the `backend.hcl` file: it's automatically created by bootstrap configuration so, when deploying the infrastructure, if it's been created, terraform will configure the backend on the S3, otherwise it'll proceed with local state.

In this file I've hidden the variable `meta.test_via_ui=true`. Infact this variable is needed by the automation scripts and I wanted to keep track of it, without creating a dedicated file. 

### Security & IAM

Following the principle of **least privilege**, I focused on designing the right permission to each resource.

- **Lambda Reader**: Policy with only `dynamodb:GetItem`, `dynamodb:Query`, `dynamodb:Scan` on the table (and indexes); `logs:CreateLogStream`, `logs:PutLogEvents` limited to its own log group.
- **Lambda Writer**: Policy with only `dynamodb:PutItem` on the table; same log permissions on its own log group.
- **KMS**: Policy that allows the key to be used only by DynamoDB in the same account/region (`kms:ViaService`, `kms:CallerAccount`).
- **S3 (state bucket)**: Block public access, versioning, and encryption; no public policy.
- **S3 (website)**: Policy that allows only `s3:GetObject` on bucket objects; CORS on the API limited to the site origin.

### Observability

I designed the infrastructure to keep track of:
- **Lambda functions**: lambda code is full of `print` blocks for debugging and following lambda execution step by step;
- **API Gateay**: configured throttling (burst/rate); access log with `requestId`, `requestTime`, `routeKey`, `status`, `integrationError`, `errorMessage`.

### Automations
Makefiles are considered a bonus, but since I'm not proficient in this kind of automation, I found it easier, faster, and more appropriate to build these Lambdas using Terraform’s built-in packaging functionality. For simple Lambdas with no external dependencies, Terraform’s native “build function” capability is perfectly suited to the task.

<br>

As part of the automation effort, I chose to implement setup and cleanup scripts to make it easier for testers to approach and work with the infrastructure.
___

## 7. Future Improvements (Vision)

### High Availability

- **CloudFront CDN** — Placing an **Amazon CloudFront** distribution in front of the S3-hosted test site improves availability and global reach: requests are served from the PoPs (Points of Presence) closest to the user, reducing latency and load on the S3 origin, and providing a single, stable HTTPS endpoint. In the event of a temporary origin unavailability, the CDN cache can continue to serve the static resources already cached, increasing the perceived resilience of the test site.

### Scalability

- **DynamoDB Accelerator (DAX)** — for massive, low-latency reads on `GET /messages` and `GET /messages/{id}`; in-memory cache in front of DynamoDB without modifying the Lambda code.
- **Caching on API Gateway** — Enabling caching on GET routes to reduce reads to DynamoDB.
- **DynamoDB** — Evaluate provisioned capacity (RCU/WCU) if load becomes predictable; maintain on-demand for variable loads.

### Disaster Recovery

- **DynamoDB Replicas** — Enable **DynamoDB Global Tables** to replicate the message table to one or more secondary regions. In the event of a failure or unavailability of the primary region, traffic can be directed to the replica (failover) and reduced RTO/RPO.
- **Backup Policies** — For the DynamoDB table: enable **Point-in-Time Recovery (PITR)** for continuous restores; define periodic **on-demand backups** (e.g., daily or pre-release) via AWS Backup. Versioning is already enabled for the Terraform (S3) state; evaluate lifecycle policies and cross-region replication of the bucket state for infrastructure disaster recovery scenarios.

### Security

- **AWS WAF** — Associate a Web Application Firewall with the API Gateway to protect against common attacks (SQL injection, XSS, advanced rate limiting, geo-blocking).
- **Authentication** — Integrate Cognito or Lambda authorizer (JWT/OAuth) to secure routes in production.

### CI/CD

- **Deployment automation** via **GitHub Actions** or **AWS CodePipeline**:
- On push to `main`: `terraform plan` (or apply in staging environment).
- Frontend build and upload to S3 in pipeline.
- Manual approval for apply in production.

___

## 8. Project CleanUp

**Recommendation**: follow the steps relative to your followed setup mode.

### Automatic CleanUp

This field is thought for making tester life easier. I've realized all the necessary scripts to deploy the infrastructure and destroy it after completing the tests.

**CRITICAL** - make it sure to respect all the prerequisites written above, otherwise the scripts will fail saying `Dependency not installed`

#### Mac users

Enter the repository of the project by using `cd` command 

1. Find the project directory in your "finder" 
2. Copy the whole path of the directory
3. Launch terminal app with cmd+space and type "terminal" (sudo role not necessary)
4. type:
    ```
    cd <directory path>
    ```

Make the scripts executable:
```
chmod +x macos_linux_scripts/destroy_infrastructure.sh
```

then run the destroying script:
```
./macos_linux_scripts/destroy_infrastructure.sh
```

To cleanup the whole project follow these steps:

`? Select AWS profile: (Use arrow keys)` 

Navigate with up/down arrow keys to the aws profile you want to use for deploying the infrastructure

`? AWS region: eu-central-1` ✅

`? This will DESTROY the entire infrastructure and delete S3 content. Continue? (y/N)` 

Type `y` to release the ui website

Once finished on the destroying you'll be able to delete the directory. 

#### Windows users

Enter the repository of the project by using `cd` command 

1. Find the project directory in your "file explorer" 
2. Copy the whole path of the directory
3. Launch powershell app (admin role not necessary)
4. type:
    ```
    cd <directory path>
    ```

then run the destroying script:
```
.\windows_scripts\destroy_infrastructure_win.cmd
```

To cleanup the whole project follow these steps:

`? Select AWS profile: (Use arrow keys)` 

Navigate with up/down arrow keys to the aws profile you want to use for deploying the infrastructure

`? AWS region: eu-central-1` ✅

`? This will DESTROY the entire infrastructure and delete S3 content. Continue? (y/N)` 

Type `y` to release the ui website

Once finished on the destroying you'll be able to delete the directory. 

### Manual Cleanup

For destroying manually the infrastructure follow these steps:

1. If *test_via_ui=true* S3 Website needs to be empty. run this command:
    ```
    aws s3 rm s3://marraffa-satispay-site/ --recursive --profile <AWS profile>
    ``` 

2. Enter the repository of the project by using `cd` command 

    1. Find the project directory in your "finder" or "file explorer" 
    2. Copy the whole path of the directory
    3. Launch terminal app or Powershell (sudo/admin role not necessary)
    4. type:
        ```
        cd <directory path>
        ```
3. Update the following commands with your used aws profile and testing mode.
For **mac users**:
    ```
    terraform -chdir=./cloud_infrastructure/infrastructure destroy -auto-approve -var="profile=<your AWS Profile>" -var="test_via_ui=<true/false>"
    ```
    For **windows users**:
    ```
    terraform -chdir=.\cloud_infrastructure\infrastructure destroy -auto-approve -var="profile=<your AWS Profile>" -var="test_via_ui=<true/false>"
    ```