/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 */

import { CloudFrontRequestHandler } from "aws-lambda";
import { Authenticator, AuthenticatorParams } from "cognito-at-edge";
import { readFileSync } from "fs";

function getAuthenticatorParams(): AuthenticatorParams {
  return JSON.parse(
    readFileSync(`${__dirname}/config.json`).toString("utf8"),
  ) as AuthenticatorParams;
}

const authenticatorParams = getAuthenticatorParams();
if (
  ["info", "debug", "trace"].includes(authenticatorParams.logLevel || "info")
) {
  console.info("Started lambda check-auth");
}
if (["debug", "trace"].includes(authenticatorParams.logLevel || "info")) {
  console.debug("Authenticator params:", authenticatorParams);
}

export const handler: CloudFrontRequestHandler = async (event) => {
  if (
    ["info", "debug", "trace"].includes(authenticatorParams.logLevel || "info")
  ) {
    console.info("Called lambda check-auth");
  }
  if (["debug", "trace"].includes(authenticatorParams.logLevel || "info")) {
    console.debug("Event:", event);
  }

  // Before authentication, rewrite paths to the index.html file
  const request = event.Records[0].cf.request;
  const uri = request.uri;

  // Check whether the URI is missing a file name.
  if (uri.endsWith("/")) {
    request.uri += "index.html";
  }
  // Check whether the URI is missing a file extension.
  else if (!uri.includes(".")) {
    request.uri += "/index.html";
  }

  const authenticator = new Authenticator(authenticatorParams);
  return authenticator.handle(event);
};
