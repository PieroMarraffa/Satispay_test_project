# Candidate Project for Satispay
*Author: Piero Marraffa*

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

In the assignement I was ask to decide between one single lambda to manage API calls or devide the management between two of them. So I've gone for two for respecting the assignement of **least privilege**. Infact by doing this I could have **use two separate IAM roles** and assign to each lambda just the "allows" it need

### API Gateway

For reaching the lambdas, I've opted for **AWS API Gateway HTTP v2 version**. In fact, besides the fact that I've already used it in my previous projects, it was the **simplest and most efficient** way to implement the API requestes. I've used proxy integration, CORS config and lambda implementation to configure the entire service.

### KMS integration

Speaking of security, I immediately thought of DynamoDB's **data-at-rest encryption**. I'd never used this service before, but I was familiar with its implementation, having studied it during my AWS certification preparation.

### Terraform state

Even if not mandatory, I've written the code for releasing an S3 for storing tf state of the project. I use it by default in the configuration scripts, but the infrastructure still works if manually released without the backend S3.

### UI and Automations

Even if not requested, I've implemented a react web app and multiple automation files just to make configuration, testing and destroying the infrastructure easier and more agile for interviewer. Wanted to focus on infrastructure design, implementation and testing, I've used AI tools to help me implement this features. Of course the infrastructure is still configurable and testable in manual ways that I'll explain in the relative chapter of this documentation.

___

## 3. Architecture Diagram and Flow

By using draw.io online tool I've realised the following architectur design schema. 

![Cloud Design](cloud_architecture.jpg)

### Infrastructure Flow
1. **Client** send a CURL request to the API Gateway (if using UI for testing I've linked the Website endpoint to API GTW CORS configuration) 
2. Depending on the request, **API GTW** invoke the right lambda by using its lambda integration and permission
3. **Lambdas** access the DynamoDB tables with **IAM Role** restricted to the least possible privilege 
4. **DynamoDB** persist data and encrypt them at rest with **KMS Key**
5. Lambda functions and API Gateway log to **AWS CloudWatch Logs** in their dedicate Log Groups. (IAM Roles provide them the possibility to perform these actions)

___

## 4. Getting Started

### Prerequisites

- **AWS CLI** - [Installed](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) and configured (`aws configure --profile <profile_name>`) 
- **Terraform** - [Installed](https://developer.hashicorp.com/terraform/install) and inserted in path (follow this [doc](https://terraform-tutorial.schoolofdevops.com/00-environment-setup/))
- **Python 3** — just for setup/destroy scripts; [python.org](https://www.python.org/downloads/).
- **Node.js / npm** — just for UI relise: [nodejs.org](https://nodejs.org/).

### Automatic Setup

This field is thought for making tester life easier. I've realized all the script necessaries to deploy the infrastructure and destroy it after completing the tests.

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
chmod +x macos_linux_installation/first_configuration.sh
chmod +x macos_linux_installation/destroy_infrastructure.sh
```

Than run the configuration script:
```
./macos_linux_installation/first_configuration.sh
```

To setup the whole project follow the following steps:

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

Than run the configuration script:
```
.\windows_installation\first_configuration.cmd
```

To setup the whole project follow the following steps:

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
**DISCLAIMER** - setup the project manually only if you're proficient in `Terraform` and `command line tools`, it may be a bit difficult.

For setupping manually the infrastructure follow these steps:

1. Enter the repository of the project by using `cd` command 

    1. Find the project directory in your "file explorer" 
    2. Copy the whole path of the directory
    3. Launch powershell app (admin role not necessary)
    4. type:
        ```
        cd <directory path>
        ```
2. update the following command with your desired aws profile and testing mode. I would advise to release the ui website (*test_via_ui=true*), but it's on your discreption, it won't change the test outcome.
For **mac users**:
    ```
    terraform -chdir=./cloud_infrastructure/infrastructure init \
    -var="profile=<your AWS Profile>" \
    -var="test_via_ui=<true/false>"
    ```
    For **windows users**:
    ```
    terraform -chdir=.\cloud_infrastructure\infrastructure init \
    -var="profile=<your AWS Profile>" \
    -var="test_via_ui=<true/false>"
    ```
3. Now let's apply the infrastructure:
For **mac users**:
    ```
    terraform -chdir=./cloud_infrastructure/infrastructure apply -auto-approve \
    -var="profile=<your AWS Profile>" \
    -var="test_via_ui=<true/false>"
    ```
    For **windows users**:
    ```
    terraform -chdir=.\cloud_infrastructure\infrastructure apply -auto-approve \
    -var="profile=<your AWS Profile>" \
    -var="test_via_ui=<true/false>"
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
2. send in terminal app the following command:
    ```
    export VITE_API_BASE_URL=...
    ```
    paste here the text you copied before
3. for creating a new message:
    ```
    curl -X POST "$VITE_API_BASE_URL/messages" \
        -H "Content-Type: application/json" \
        -d '{"text":"Hello world","title":"First meassage"}'
    ```
4. for listing all messages:
    ```
    curl "$VITE_API_BASE_URL/messages"
    ```
5. for reading a message by it's id:
    ```
    curl "$VITE_API_BASE_URL/messages/<id>"
    ```
    you'll find the id from the list api response