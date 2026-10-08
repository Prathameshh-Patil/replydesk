import { Suspense } from "react";
import { NewMessageForm } from "./NewMessageForm";

export default function NewMessagePage() {
  return (
    <Suspense>
      <NewMessageForm />
    </Suspense>
  );
}
