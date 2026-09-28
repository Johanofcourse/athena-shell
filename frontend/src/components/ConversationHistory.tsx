import type { ConversationTurn } from "../types";

interface Props {
  history: ConversationTurn[];
}

/** Visible trace that context is actually being carried between turns -
 * not just true in the backend, but shown, same reasoning as the
 * InterpretationPanel. */
export function ConversationHistory({ history }: Props) {
  if (history.length === 0) return null;

  return (
    <ul className="conversation-history">
      {history.map((turn, i) => (
        <li key={i}>{turn.query}</li>
      ))}
    </ul>
  );
}
