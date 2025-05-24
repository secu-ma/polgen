import {AuthenticatorParams} from "cognito-at-edge";
import {readFileSync} from "fs";

export function getAuthenticatorParams(): AuthenticatorParams {
  return JSON.parse(
    readFileSync(`${__dirname}/config.json`).toString("utf8")
  ) as AuthenticatorParams;
}
