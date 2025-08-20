import Lake
open Lake DSL

package «ax-mcp» {
  -- add package configuration options here
}

require mathlib from git "https://github.com/leanprover-community/mathlib4.git" @ "v4.8.0"

@[default_target]
lean_lib «ax-mcp» {
  -- add library configuration options here
}
