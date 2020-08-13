This project was bootstrapped with [Create React App](https://github.com/facebook/create-react-app).

It was originally designed to run on Firebase with google cloud run. Some settings may need to be modified to work on AWS.

## Basic Structure
* `api`: flask server code. 
* `public`: template html and other public documents
* `src`: the bulk of the react.js logic lives here
* `package.json`: some settings live here that glue everything together

## Run Local Webserver

* First, make sure you have a python environment with the requirements listed in `api/requirements.txt`
* Next, make sure you have node.js installed and that you have all of the modules from `package-lock.json` installed for this project. Run `npm install` to install dependencies.

### `yarn start`

Runs the UI in the development mode.<br />
Open [http://localhost:3000](http://localhost:3000) to view it in the browser.

The page will reload if you make edits.<br />
You will also see any lint errors in the console.

### `yarn start-api-local`

Starts the flask server. The flask server runs through port 5000 by default. The react app knows to listen for port 5000 from the `proxy` setting in `package.json`

## Productionalization 

### `yarn build`

Builds the app for production to the `build` folder.<br />
It correctly bundles React in production mode and optimizes the build for the best performance.

The build is minified and the filenames include the hashes.<br />
Your app is ready to be deployed!

See the section about [deployment](https://facebook.github.io/create-react-app/docs/deployment) for more information.

### `Dockerfile`

Contains a docker container that can run the flask server. 