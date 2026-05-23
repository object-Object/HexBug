import type { DiscordSDK } from "@discord/embedded-app-sdk";
import * as jose from "jose";
import { use } from "react";

import { useDiscordSDK } from "./useDiscordSDK";

export function useDiscordAuth() {
  const discordSDK = useDiscordSDK();
  authPromise ??= authenticate(discordSDK);
  return use(authPromise);
}

let authPromise: ReturnType<typeof authenticate> | undefined;

const publicKeyPromise = jose.importSPKI(
  import.meta.env.VITE_JWT_PUBLIC_KEY,
  "Ed25519",
);

// Keep in sync with bot/src/HexBug/cogs/api.py
interface ActivityTokenRequest {
  code: string;
}

// Keep in sync with bot/src/HexBug/cogs/api.py
interface ActivityTokenResponse {
  access_token: string;
  api_token: string;
}

// Keep in sync with bot/src/HexBug/cogs/api.py
interface ActivityAPIToken {
  user_id: string;
}

async function authenticate(discordSDK: DiscordSDK) {
  const authOutput = await discordSDK.commands.authorize({
    client_id: import.meta.env.VITE_CLIENT_ID,
    response_type: "code",
    prompt: "none",
    scope: ["identify"],
  });

  const tokenResponse = await fetch("/api/activity/token", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(authOutput satisfies ActivityTokenRequest),
  });
  const { access_token, api_token } =
    (await tokenResponse.json()) as ActivityTokenResponse;

  const publicKey = await publicKeyPromise;
  const decryptResult = await jose.jwtVerify<ActivityAPIToken>(
    api_token,
    publicKey,
  );
  const api_token_value: ActivityAPIToken = decryptResult.payload;

  const authResponse = await discordSDK.commands.authenticate({
    access_token,
  });

  if (api_token_value.user_id !== authResponse.user.id) {
    throw new Error(
      `Mismatched user id in API token: expected ${authResponse.user.id}, got ${api_token_value.user_id}`,
    );
  }

  return {
    api_token,
    api_token_value,
    ...authResponse,
  };
}
