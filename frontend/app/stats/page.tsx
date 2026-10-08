import { Suspense } from "react";
import { RequireLogin } from "@/components/RequireLogin";
import { StatsView } from "./StatsView";

export default function StatsPage() {
  return (
    <Suspense>
      <RequireLogin>
        <StatsView />
      </RequireLogin>
    </Suspense>
  );
}
