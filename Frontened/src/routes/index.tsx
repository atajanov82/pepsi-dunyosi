import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Pepsi Dunyosi" },
      { name: "description", content: "Промо-приложение Pepsi Dunyosi — вводи коды, копи рубли, выигрывай призы." },
      { property: "og:title", content: "Pepsi Dunyosi" },
      { property: "og:description", content: "Промо-приложение Pepsi Dunyosi — вводи коды, копи рубли, выигрывай призы." },
    ],
  }),
  component: Index,
});

function Index() {
  return (
    <iframe
      src="/pepsi.html"
      title="Pepsi Dunyosi"
      style={{ border: 0, width: "100vw", height: "100vh", display: "block" }}
    />
  );
}
