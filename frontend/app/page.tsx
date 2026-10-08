import { Suspense } from "react";
import { RequireLogin } from "@/components/RequireLogin";
import { Inbox } from "./Inbox";

export default function InboxPage() {
  return (
    <Suspense>
      <RequireLogin>
        <Inbox />
      </RequireLogin>
    </Suspense>
  );
}
