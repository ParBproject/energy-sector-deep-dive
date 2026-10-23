import { writeFileSync } from "node:fs";
import { tokens } from "../src/design/tokens";

writeFileSync(new URL("../src/design/tokens.json", import.meta.url), JSON.stringify(tokens, null, 2) + "\n");
console.log("wrote web/src/design/tokens.json");
