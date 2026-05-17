import { DiscordSDK, Events } from "@discord/embedded-app-sdk";
import { use } from "react";

export function useDiscordSDK(): DiscordSDK {
  use(authPromise);
  return use(discordSDKPromise);
}

// https://stackoverflow.com/a/71560711
export type DiscordSDKSubscribeParameters<T extends Events> = Parameters<
  typeof discordSDK.subscribe<T>
>;

const discordSDK = new DiscordSDK(import.meta.env.VITE_CLIENT_ID);

const discordSDKPromise = discordSDK.ready().then(() => discordSDK);
const authPromise = authenticate();

interface TokenResponse {
  access_token: string;
}

async function authenticate() {
  await discordSDKPromise;

  const { code } = await discordSDK.commands.authorize({
    client_id: import.meta.env.VITE_CLIENT_ID,
    response_type: "code",
    prompt: "none",
    scope: ["identify"],
  });

  const response = await fetch("/api/activity/token", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code }),
  });
  const { access_token } = (await response.json()) as TokenResponse;

  return await discordSDK.commands.authenticate({ access_token });
}
