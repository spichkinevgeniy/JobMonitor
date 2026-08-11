import {
  type RefObject,
  useCallback,
  useEffect,
  useRef,
} from "react";

interface UseFocusedInputScrollParams {
  scrollContainerRef: RefObject<HTMLElement | null>;
  inputRef: RefObject<HTMLInputElement | null>;
  topOffset?: number;
}

const DEFAULT_TOP_OFFSET = 16;
const KEYBOARD_SETTLE_DELAY_MS = 350;

export const useFocusedInputScroll = ({
  scrollContainerRef,
  inputRef,
  topOffset = DEFAULT_TOP_OFFSET,
}: UseFocusedInputScrollParams) => {
  const fallbackTimeoutRef = useRef<number | null>(null);

  const scrollInputIntoView = useCallback(
    (behavior: ScrollBehavior = "auto") => {
      const container = scrollContainerRef.current;
      const input = inputRef.current;

      if (!container || !input) {
        return;
      }

      const containerRect = container.getBoundingClientRect();
      const inputRect = input.getBoundingClientRect();

      const targetScrollTop =
        container.scrollTop +
        inputRect.top -
        containerRect.top -
        topOffset;

      container.scrollTo({
        top: Math.max(0, targetScrollTop),
        behavior,
      });
    },
    [inputRef, scrollContainerRef, topOffset],
  );

  const handleFocus = useCallback(() => {
    if (fallbackTimeoutRef.current !== null) {
      window.clearTimeout(fallbackTimeoutRef.current);
    }

    requestAnimationFrame(() => {
      scrollInputIntoView("smooth");
    });

    // Страховка для Telegram/iOS WebView:
    // иногда финальный размер viewport приходит с задержкой.
    fallbackTimeoutRef.current = window.setTimeout(() => {
      scrollInputIntoView("auto");
      fallbackTimeoutRef.current = null;
    }, KEYBOARD_SETTLE_DELAY_MS);
  }, [scrollInputIntoView]);

  useEffect(() => {
    const viewport = window.visualViewport;

    if (!viewport) {
      return;
    }

    const handleViewportChange = () => {
      if (document.activeElement !== inputRef.current) {
        return;
      }

      requestAnimationFrame(() => {
        scrollInputIntoView("auto");
      });
    };

    viewport.addEventListener("resize", handleViewportChange);
    viewport.addEventListener("scroll", handleViewportChange);

    return () => {
      viewport.removeEventListener("resize", handleViewportChange);
      viewport.removeEventListener("scroll", handleViewportChange);
    };
  }, [inputRef, scrollInputIntoView]);

  useEffect(() => {
    return () => {
      if (fallbackTimeoutRef.current !== null) {
        window.clearTimeout(fallbackTimeoutRef.current);
      }
    };
  }, []);

  return {
    handleFocus,
  };
};