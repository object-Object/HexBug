import { Events } from "@discord/embedded-app-sdk";
import { useState } from "react";

import { useDiscordEventListener } from "./useDiscordEventListener";

// https://docs.discord.com/developers/developer-tools/embedded-app-sdk#layoutmodetypeobject
export enum DiscordLayoutMode {
  UNHANDLED = -1,
  FOCUSED = 0,
  PIP = 1,
  GRID = 2,
}

export function useDiscordLayoutMode(): DiscordLayoutMode {
  const [layoutMode, setLayoutMode] = useState(DiscordLayoutMode.FOCUSED);

  useDiscordEventListener(
    Events.ACTIVITY_LAYOUT_MODE_UPDATE,
    ({ layout_mode }) => {
      setLayoutMode(layout_mode);
    },
  );

  return layoutMode;
}
