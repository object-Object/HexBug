import { DiscordSDK, Events } from "@discord/embedded-app-sdk";
import { use } from "react";

export function useDiscordSDK(): DiscordSDK {
  discordSDKPromise ??= discordSDK.ready().then(() => discordSDK);
  return use(discordSDKPromise);
}

// https://stackoverflow.com/a/71560711
export type DiscordSDKSubscribeParameters<T extends Events> = Parameters<
  typeof discordSDK.subscribe<T>
>;

const discordSDK = new DiscordSDK(import.meta.env.VITE_CLIENT_ID);

export let discordSDKPromise: Promise<DiscordSDK>;
