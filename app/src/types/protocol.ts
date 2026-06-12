/* GERADO por scripts/gen-types.sh a partir dos modelos Pydantic — não editar à mão. */

export type V = number;
export type Type = "hello";
export type Id = string;
export type Token = string;
export type DeviceId = string;
export type DeviceName = string;
export type V1 = number;
export type Type1 = "deck.get";
export type Id1 = string;
export type V2 = number;
export type Type2 = "action.trigger";
export type Id2 = string;
export type ButtonId = string;
export type V3 = number;
export type Type3 = "ping";
export type Id3 = string;
export type V4 = number;
export type Type4 = "deck.save";
export type Id4 = string;
export type Version = number;
export type ActiveProfile = string;
export type Id5 = string;
export type Name = string;
export type Id6 = string;
export type Name1 = string;
export type Cols = number;
export type Rows = number;
export type Id7 = string;
export type Col = number;
export type Row = number;
export type Label = string;
export type Icon = string;
export type Color = string;
export type Action =
  | OpenAppAction
  | OpenPathAction
  | OpenUrlAction
  | HotkeyAction
  | TextAction
  | ShellAction
  | MacroAction;
export type Type5 = "open_app";
/**
 * @minItems 1
 */
export type Command = [string, ...string[]];
export type Type6 = "open_path";
export type Path = string;
export type Type7 = "open_url";
export type Url = string;
export type Type8 = "hotkey";
/**
 * @minItems 1
 */
export type Keys = [string, ...string[]];
export type Type9 = "text";
export type Text = string;
export type Type10 = "shell";
export type Command1 = string;
export type Type11 = "macro";
/**
 * @minItems 1
 * @maxItems 50
 */
export type Steps = [
  OpenAppAction | OpenPathAction | OpenUrlAction | HotkeyAction | TextAction | ShellAction | DelayStep,
  ...(OpenAppAction | OpenPathAction | OpenUrlAction | HotkeyAction | TextAction | ShellAction | DelayStep)[]
];
export type Type12 = "delay";
export type Ms = number;
export type State = ("mic_muted" | "audio_muted") | null;
export type Buttons = Button[];
export type Pages = Page[];
export type Profiles = Profile[];
export type AllowShell = boolean;
export type V5 = number;
export type Type13 = "hello.ok";
export type Id8 = string;
export type AgentVersion = string;
export type ActiveProfile1 = string;
export type V6 = number;
export type Type14 = "hello.denied";
export type Id9 = string;
export type Reason = string;
export type V7 = number;
export type Type15 = "deck.layout";
export type Id10 = string;
export type V8 = number;
export type Type16 = "action.result";
export type Id11 = string;
export type ButtonId1 = string;
export type Status = "ok" | "error";
export type Message = string;
export type V9 = number;
export type Type17 = "state.update";
export type Id12 = string;
export type ButtonId2 = string;
export type Active = boolean;
export type V10 = number;
export type Type18 = "pong";
export type Id13 = string;
export type V11 = number;
export type Type19 = "error";
export type Id14 = string | null;
export type Message1 = string;
export type Version1 = number;
export type ActiveProfile2 = string;
export type Profiles1 = Profile[];
export type AllowShell1 = boolean;

export interface Protocol {
  client: HelloMessage | DeckGetMessage | ActionTriggerMessage | PingMessage | DeckSaveMessage;
  server:
    | HelloOkMessage
    | HelloDeniedMessage
    | DeckLayoutMessage
    | ActionResultMessage
    | StateUpdateMessage
    | PongMessage
    | ErrorMessage;
  config: DeckConfig1;
}
export interface HelloMessage {
  v?: V;
  type?: Type;
  id: Id;
  payload: HelloPayload;
}
export interface HelloPayload {
  token: Token;
  device_id: DeviceId;
  device_name?: DeviceName;
}
export interface DeckGetMessage {
  v?: V1;
  type?: Type1;
  id: Id1;
}
export interface ActionTriggerMessage {
  v?: V2;
  type?: Type2;
  id: Id2;
  payload: ActionTriggerPayload;
}
export interface ActionTriggerPayload {
  button_id: ButtonId;
}
export interface PingMessage {
  v?: V3;
  type?: Type3;
  id: Id3;
}
export interface DeckSaveMessage {
  v?: V4;
  type?: Type4;
  id: Id4;
  payload: DeckConfig;
}
export interface DeckConfig {
  version?: Version;
  active_profile: ActiveProfile;
  profiles?: Profiles;
  allow_shell?: AllowShell;
}
export interface Profile {
  id: Id5;
  name: Name;
  pages?: Pages;
}
export interface Page {
  id: Id6;
  name: Name1;
  grid?: Grid;
  buttons?: Buttons;
}
export interface Grid {
  cols?: Cols;
  rows?: Rows;
}
export interface Button {
  id: Id7;
  position: Position;
  label: Label;
  icon?: Icon;
  color?: Color;
  action: Action;
  state?: State;
}
export interface Position {
  col: Col;
  row: Row;
}
export interface OpenAppAction {
  type?: Type5;
  command: Command;
}
export interface OpenPathAction {
  type?: Type6;
  path: Path;
}
export interface OpenUrlAction {
  type?: Type7;
  url: Url;
}
export interface HotkeyAction {
  type?: Type8;
  keys: Keys;
}
export interface TextAction {
  type?: Type9;
  text: Text;
}
export interface ShellAction {
  type?: Type10;
  command: Command1;
}
export interface MacroAction {
  type?: Type11;
  steps: Steps;
}
export interface DelayStep {
  type?: Type12;
  ms: Ms;
}
export interface HelloOkMessage {
  v?: V5;
  type?: Type13;
  id: Id8;
  payload: HelloOkPayload;
}
export interface HelloOkPayload {
  agent_version: AgentVersion;
  active_profile: ActiveProfile1;
}
export interface HelloDeniedMessage {
  v?: V6;
  type?: Type14;
  id: Id9;
  payload: HelloDeniedPayload;
}
export interface HelloDeniedPayload {
  reason: Reason;
}
export interface DeckLayoutMessage {
  v?: V7;
  type?: Type15;
  id: Id10;
  payload: DeckConfig;
}
export interface ActionResultMessage {
  v?: V8;
  type?: Type16;
  id: Id11;
  payload: ActionResultPayload;
}
export interface ActionResultPayload {
  button_id: ButtonId1;
  status: Status;
  message?: Message;
}
export interface StateUpdateMessage {
  v?: V9;
  type?: Type17;
  id: Id12;
  payload: StateUpdatePayload;
}
export interface StateUpdatePayload {
  button_id: ButtonId2;
  active: Active;
}
export interface PongMessage {
  v?: V10;
  type?: Type18;
  id: Id13;
}
export interface ErrorMessage {
  v?: V11;
  type?: Type19;
  id?: Id14;
  payload: ErrorPayload;
}
export interface ErrorPayload {
  message: Message1;
}
export interface DeckConfig1 {
  version?: Version1;
  active_profile: ActiveProfile2;
  profiles?: Profiles1;
  allow_shell?: AllowShell1;
}
