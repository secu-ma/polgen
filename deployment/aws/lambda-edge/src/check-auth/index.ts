import {CloudFrontRequestHandler} from "aws-lambda";
import {getAuthenticatorParams} from "../shared/shared";
import {Authenticator} from "cognito-at-edge";

const authenticatorParams = getAuthenticatorParams();
if (["debug", "trace"].includes(authenticatorParams.logLevel || "info")) {
  console.debug("Authenticator params:", authenticatorParams);
}
if (["info", "debug", "trace"].includes(authenticatorParams.logLevel || "info")) {
  console.info("Started lambda check-auth");
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
