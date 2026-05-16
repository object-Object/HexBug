import type { Events } from "@discord/embedded-app-sdk";
import { useEffect, useRef } from "react";

import {
  type DiscordSDKSubscribeParameters,
  useDiscordSDK,
} from "./useDiscordSDK";

export function useDiscordEventListener<T extends Events>(
  ...args: DiscordSDKSubscribeParameters<T>
) {
  const sdk = useDiscordSDK();

  // In strict mode, the second sdk.subscribe fails if we don't first await
  // the promise returned by the sdk.unsubscribe; so use a promise chain to
  // force the subscribes and unsubscribes to run sequentially
  const promiseRef = useRef<Promise<unknown>>(Promise.resolve());

  useEffect(() => {
    promiseRef.current = promiseRef.current.then(() => sdk.subscribe(...args));
    return () => {
      promiseRef.current = promiseRef.current.then(() =>
        sdk.unsubscribe(...args),
      );
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps, react-x/exhaustive-deps
  }, [sdk, ...args]);
}
