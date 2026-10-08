import { Suspense } from "react";
import { RequireLogin } from "@/components/RequireLogin";
import { TicketView } from "./TicketView";

export default function TicketPage() {
  return (
    <Suspense>
      <RequireLogin>
        <TicketView />
      </RequireLogin>
    </Suspense>
  );
}
