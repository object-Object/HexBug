import { ControlledNumberInput } from "@hextools/react";
import { mod } from "@hextools/renderer";
import type { GuiSpellcastingSettings } from "@hextools/renderer/staffGrid";
import {
  Accordion,
  ActionIcon,
  Button,
  InputWrapper,
  Modal,
  SegmentedControl,
  Stack,
  Switch,
} from "@mantine/core";
import { useDisclosure, useMediaQuery } from "@mantine/hooks";
import { IconChevronRight, IconSettings } from "@tabler/icons-react";

import { staffGridButtonProps } from "./StaffGridControls.lib";
import styles from "./StaffGridSettings.module.css";
import type { KeysOfValue } from "./types";

export interface StaffGridSettingsProps {
  settings: GuiSpellcastingSettings;
  onSettingsChange: (value: GuiSpellcastingSettings) => unknown;
  onResetSettings: () => unknown;
  onSignInWithDiscord: (() => unknown) | null;
}

export default function StaffGridSettings({
  settings,
  onSettingsChange,
  onResetSettings,
  onSignInWithDiscord,
}: StaffGridSettingsProps) {
  const {
    guiScale,
    gridZoom,
    enableZappyPoints,
    zappyVariance,
    ctrlTogglesOffStrokeOrder,
    dotsMode,
    mouseDotsRadius,
    clickingTogglesDrawing,
  } = settings;

  const [opened, { open, close }] = useDisclosure(false);
  const isMobile = useMediaQuery("(max-width: 30em)");

  function getSetter<T extends keyof GuiSpellcastingSettings>(
    key: T,
  ): (value: GuiSpellcastingSettings[T]) => unknown {
    return (value) => {
      onSettingsChange({ ...settings, [key]: value });
    };
  }

  function getSwitchSetter<
    T extends KeysOfValue<GuiSpellcastingSettings, boolean>,
  >(key: T): (event: React.ChangeEvent<HTMLInputElement>) => unknown {
    const setter = getSetter(key);
    return (event) => {
      setter(event.currentTarget.checked);
    };
  }

  const setGuiScale = getSetter("guiScale");

  return (
    <>
      <Modal
        opened={opened}
        onClose={close}
        fullScreen={isMobile}
        title="Settings"
      >
        <Stack>
          <Button
            variant="default"
            onClick={(event) =>
              setGuiScale(mod(guiScale - 1 + (event.shiftKey ? -1 : 1), 5) + 1)
            }
          >
            GUI Scale: {guiScale}
          </Button>

          <ControlledNumberInput
            label="Grid Zoom"
            value={gridZoom}
            onChange={getSetter("gridZoom")}
            allowNegative={false}
            min={0.25}
            step={0.25}
          />

          <Switch
            label="Enable Wobbly Patterns"
            checked={enableZappyPoints}
            onChange={getSwitchSetter("enableZappyPoints")}
          />

          <Switch
            label="Ctrl Toggles Off Stroke Order"
            checked={ctrlTogglesOffStrokeOrder}
            onChange={getSwitchSetter("ctrlTogglesOffStrokeOrder")}
          />

          <Switch
            label="Clicking Toggles Drawing"
            checked={clickingTogglesDrawing}
            onChange={getSwitchSetter("clickingTogglesDrawing")}
          />

          <InputWrapper label="Grid Dots Mode" labelElement="div">
            <SegmentedControl
              value={dotsMode}
              onChange={getSetter("dotsMode")}
              data={[
                { label: "None", value: "none" },
                { label: "Around Mouse", value: "mouse" },
                { label: "Full Grid", value: "all" },
              ]}
              fullWidth
            />
          </InputWrapper>

          <Accordion
            variant="unstyled"
            classNames={{ chevron: styles.chevron }}
            chevron={<IconChevronRight />}
            chevronPosition="left"
          >
            <Accordion.Item value="value">
              <Accordion.Control>Advanced Settings</Accordion.Control>
              <Accordion.Panel>
                <Stack>
                  {enableZappyPoints && (
                    <ControlledNumberInput
                      label="Pattern Wobbliness"
                      value={zappyVariance}
                      onChange={getSetter("zappyVariance")}
                      allowNegative={false}
                      step={0.1}
                    />
                  )}

                  {dotsMode === "mouse" && (
                    <ControlledNumberInput
                      label="Mouse Dots Radius"
                      value={mouseDotsRadius}
                      onChange={getSetter("mouseDotsRadius")}
                      allowNegative={false}
                      allowDecimal={false}
                      min={1}
                    />
                  )}

                  {onSignInWithDiscord && (
                    <Button onClick={onSignInWithDiscord}>
                      Sign in with Discord
                    </Button>
                  )}

                  <Button variant="light" color="red" onClick={onResetSettings}>
                    Reset All Settings
                  </Button>
                </Stack>
              </Accordion.Panel>
            </Accordion.Item>
          </Accordion>
        </Stack>
      </Modal>

      <ActionIcon {...staffGridButtonProps} onClick={open}>
        <IconSettings />
      </ActionIcon>
    </>
  );
}
