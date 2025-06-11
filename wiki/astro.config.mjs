// @ts-check
import { defineConfig } from "astro/config";
import starlight from "@astrojs/starlight";

// https://astro.build/config
export default defineConfig({
  integrations: [
    starlight({
      title: "Polgen",
      social: [
        {
          icon: "github",
          label: "GitHub",
          href: "https://github.com/secu-ma/polgen",
        },
      ],
      sidebar: [
        {
          label: "Policies",
          autogenerate: { directory: "policies" },
        },
      ],
    }),
  ],
});
