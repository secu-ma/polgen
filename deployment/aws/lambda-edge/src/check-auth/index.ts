import {CloudFrontRequestHandler} from "aws-lambda";
import {Authenticator, AuthenticatorParams} from "cognito-at-edge";
import {readFileSync} from "fs";

function getAuthenticatorParams(): AuthenticatorParams {
  return JSON.parse(
    readFileSync(`${__dirname}/config.json`).toString("utf8")
  ) as AuthenticatorParams;
}

const authenticatorParams = getAuthenticatorParams();
if (["info", "debug", "trace"].includes(authenticatorParams.logLevel || "info")) {
  console.info("Started lambda check-auth");
}
if (["debug", "trace"].includes(authenticatorParams.logLevel || "info")) {
  console.debug("Authenticator params:", authenticatorParams);
}

export const handler: CloudFrontRequestHandler = async (event) => {
  if (["info", "debug", "trace"].includes(authenticatorParams.logLevel || "info")) {
    console.info("Called lambda check-auth");
  }
  if (["debug", "trace"].includes(authenticatorParams.logLevel || "info")) {
    console.debug("Event:", event);
  }

  const authenticator = new Authenticator(authenticatorParams);
  return authenticator.handle(event);
};
