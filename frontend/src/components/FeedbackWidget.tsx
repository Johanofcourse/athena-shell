import { useState } from "react";
import { submitFeedback } from "../api";
import type { MarketQueryFilters } from "../types";

interface Props {
  query: string;
  filters: MarketQueryFilters;
}

/** Turns real usage into eval-growth material: every rating is logged with
 * the exact query and the exact resolved filters, so a later review pass
 * can see both the question and what the model did with it - the raw
 * material for expanding the eval set beyond hand-written cases. */
export function FeedbackWidget({ query, filters }: Props) {
  const [state, setState] = useState<"idle" | "sending" | "sent" | "error">("idle");

  async function rate(rating: "up" | "down") {
    setState("sending");
    try {
      await submitFeedback(query, filters, rating);
      setState("sent");
    } catch {
      setState("error");
    }
  }

  if (state === "sent") {
    return <p className="feedback-widget feedback-sent">Thanks, logged.</p>;
  }

  return (
    <div className="feedback-widget">
      <span>Was this interpreted correctly?</span>
      <button onClick={() => rate("up")} disabled={state === "sending"}>
        Yes
      </button>
      <button onClick={() => rate("down")} disabled={state === "sending"}>
        No
      </button>
      {state === "error" && <span className="feedback-error">Couldn't save that - try again?</span>}
    </div>
  );
}
