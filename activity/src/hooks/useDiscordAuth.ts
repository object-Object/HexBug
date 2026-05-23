import type { DiscordSDK } from "@discord/embedded-app-sdk";
import { use } from "react";

import { useDiscordSDK } from "./useDiscordSDK";

export function useDiscordAuth() {
  const discordSDK = useDiscordSDK();
  authPromise ??= authenticate(discordSDK);
  return use(authPromise);
}

let authPromise: ReturnType<typeof authenticate> | undefined;

// Keep in sync with bot/src/HexBug/cogs/api.py
interface TokenRequest {
  code: string;
}

// Keep in sync with bot/src/HexBug/cogs/api.py
interface TokenResponse {
  access_token: string;
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
    body: JSON.stringify(authOutput satisfies TokenRequest),
  });
  const response = (await tokenResponse.json()) as TokenResponse;

  return await discordSDK.commands.authenticate(response);
}
