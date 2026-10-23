import "server-only";
import { Ratelimit } from "@upstash/ratelimit";
import { Redis } from "@upstash/redis";

const redis = Redis.fromEnv();
export const aiLimit = {
  free: new Ratelimit({ redis, limiter: Ratelimit.slidingWindow(20, "1 h"), prefix: "ai-free" }),
  pro: new Ratelimit({ redis, limiter: Ratelimit.slidingWindow(200, "1 h"), prefix: "ai-pro" }),
};
export const authLimit = new Ratelimit({ redis, limiter: Ratelimit.slidingWindow(5, "15 m"), prefix: "auth" });
export const emailLimit = new Ratelimit({ redis, limiter: Ratelimit.slidingWindow(3, "1 h"), prefix: "email" });
