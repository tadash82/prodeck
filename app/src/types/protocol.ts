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
export type Action = OpenAppAction | OpenPathAction | OpenUrlAction | HotkeyAction;
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
export type Buttons = Button[];
export type Pages = Page[];
export type Profiles = Profile[];
export type V5 = number;
export type Type9 = "hello.ok";
export type Id8 = string;
export type AgentVersion = string;
export type ActiveProfile1 = string;
export type V6 = number;
export type Type10 = "hello.denied";
export type Id9 = string;
export type Reason = string;
export type V7 = number;
export type Type11 = "deck.layout";
export type Id10 = string;
export type V8 = number;
export type Type12 = "action.result";
export type Id11 = string;
export type ButtonId1 = string;
export type Status = "ok" | "error";
export type Message = string;
export type V9 = number;
export type Type13 = "pong";
export type Id12 = string;
export type V10 = number;
export type Type14 = "error";
export type Id13 = string | null;
export type Message1 = string;
export type Version1 = number;
export type ActiveProfile2 = string;
export type Profiles1 = Profile[];

export interface Protocol {
  client: HelloMessage | DeckGetMessage | ActionTriggerMessage | PingMessage | DeckSaveMessage;
  server: HelloOkMessage | HelloDeniedMessage | DeckLayoutMessage | ActionResultMessage | PongMessage | ErrorMessage;
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
export interface HelloOkMessage {
  v?: V5;
  type?: Type9;
  id: Id8;
  payload: HelloOkPayload;
}
export interface HelloOkPayload {
  agent_version: AgentVersion;
  active_profile: ActiveProfile1;
}
export interface HelloDeniedMessage {
  v?: V6;
  type?: Type10;
  id: Id9;
  payload: HelloDeniedPayload;
}
export interface HelloDeniedPayload {
  reason: Reason;
}
export interface DeckLayoutMessage {
  v?: V7;
  type?: Type11;
  id: Id10;
  payload: DeckConfig;
}
export interface ActionResultMessage {
  v?: V8;
  type?: Type12;
  id: Id11;
  payload: ActionResultPayload;
}
export interface ActionResultPayload {
  button_id: ButtonId1;
  status: Status;
  message?: Message;
}
export interface PongMessage {
  v?: V9;
  type?: Type13;
  id: Id12;
}
export interface ErrorMessage {
  v?: V10;
  type?: Type14;
  id?: Id13;
  payload: ErrorPayload;
}
export interface ErrorPayload {
  message: Message1;
}
export interface DeckConfig1 {
  version?: Version1;
  active_profile: ActiveProfile2;
  profiles?: Profiles1;
}
