// https://www.totaltypescript.com/get-keys-of-an-object-where-values-are-of-a-given-type
export type KeysOfValue<T, ConditionT> = {
  [K in keyof T]: T[K] extends ConditionT ? K : never;
}[keyof T];
