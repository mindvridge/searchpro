"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";
import { ChevronRight, ChevronLeft, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const BUSINESS_TYPES = [
  "예비창업자",
  "1년이내",
  "3년이내",
  "7년이내",
  "제한없음",
];

const INDUSTRIES = [
  "IT/SW",
  "제조",
  "바이오/의료",
  "에너지/환경",
  "문화/콘텐츠",
  "농업/식품",
  "유통/물류",
  "교육",
  "금융",
  "기타",
];

const REGIONS = [
  "서울", "경기", "인천", "부산", "대구", "광주",
  "대전", "울산", "세종", "강원", "충북", "충남",
  "전북", "전남", "경북", "경남", "제주",
];

const INTERESTS = [
  "창업", "R&D", "수출", "마케팅", "인력",
  "시설/공간", "금융/투자", "컨설팅",
];

export default function OnboardingPage() {
  const router = useRouter();
  const { data: session } = useSession();
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);

  const [businessType, setBusinessType] = useState("");
  const [industry, setIndustry] = useState("");
  const [region, setRegion] = useState("");
  const [companyAge, setCompanyAge] = useState("");
  const [employeeCount, setEmployeeCount] = useState("");
  const [interests, setInterests] = useState<string[]>([]);

  const toggleInterest = (item: string) => {
    setInterests((prev) =>
      prev.includes(item) ? prev.filter((i) => i !== item) : [...prev, item]
    );
  };

  const handleSubmit = async () => {
    setLoading(true);
    const profile = {
      business_type: businessType,
      industry,
      region,
      company_age_years: parseInt(companyAge) || 0,
      employee_count: parseInt(employeeCount) || 0,
      interests,
    };

    await fetch(`${API_URL}/api/v1/auth/profile`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${(session as any)?.accessToken || ""}`,
      },
      body: JSON.stringify({ profile }),
    });

    router.push("/");
    setLoading(false);
  };

  const steps = [
    // Step 1: 사업자 유형
    {
      title: "사업자 유형을 선택해주세요",
      subtitle: "맞춤 지원사업을 추천해 드립니다",
      content: (
        <div className="grid grid-cols-1 gap-2">
          {BUSINESS_TYPES.map((type) => (
            <Button
              key={type}
              variant={businessType === type ? "default" : "outline"}
              className="justify-start"
              onClick={() => setBusinessType(type)}
            >
              {type}
            </Button>
          ))}
        </div>
      ),
    },
    // Step 2: 업종 & 지역
    {
      title: "업종과 지역을 알려주세요",
      subtitle: "관련 지원사업을 필터링합니다",
      content: (
        <div className="space-y-4">
          <div>
            <p className="text-sm font-medium mb-2">업종</p>
            <div className="flex flex-wrap gap-2">
              {INDUSTRIES.map((ind) => (
                <Badge
                  key={ind}
                  variant={industry === ind ? "default" : "outline"}
                  className="cursor-pointer"
                  onClick={() => setIndustry(ind)}
                >
                  {ind}
                </Badge>
              ))}
            </div>
          </div>
          <div>
            <p className="text-sm font-medium mb-2">지역</p>
            <div className="flex flex-wrap gap-2">
              {REGIONS.map((r) => (
                <Badge
                  key={r}
                  variant={region === r ? "default" : "outline"}
                  className="cursor-pointer"
                  onClick={() => setRegion(r)}
                >
                  {r}
                </Badge>
              ))}
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <p className="text-sm font-medium mb-1">업력 (년)</p>
              <Input
                type="number"
                placeholder="0"
                min={0}
                value={companyAge}
                onChange={(e) => setCompanyAge(e.target.value)}
              />
            </div>
            <div>
              <p className="text-sm font-medium mb-1">직원 수</p>
              <Input
                type="number"
                placeholder="0"
                min={0}
                value={employeeCount}
                onChange={(e) => setEmployeeCount(e.target.value)}
              />
            </div>
          </div>
        </div>
      ),
    },
    // Step 3: 관심 분야
    {
      title: "관심 분야를 선택해주세요",
      subtitle: "복수 선택이 가능합니다",
      content: (
        <div className="flex flex-wrap gap-2">
          {INTERESTS.map((item) => (
            <Badge
              key={item}
              variant={interests.includes(item) ? "default" : "outline"}
              className="cursor-pointer text-sm px-4 py-2"
              onClick={() => toggleInterest(item)}
            >
              {interests.includes(item) && <Check className="mr-1 h-3 w-3" />}
              {item}
            </Badge>
          ))}
        </div>
      ),
    },
  ];

  const isLastStep = step === steps.length - 1;

  return (
    <div className="flex min-h-[60vh] items-center justify-center">
      <Card className="w-full max-w-lg">
        <CardHeader className="text-center">
          <div className="flex justify-center gap-2 mb-4">
            {steps.map((_, i) => (
              <div
                key={i}
                className={`h-2 w-8 rounded-full ${
                  i <= step ? "bg-primary" : "bg-muted"
                }`}
              />
            ))}
          </div>
          <CardTitle>{steps[step].title}</CardTitle>
          <p className="text-sm text-muted-foreground">
            {steps[step].subtitle}
          </p>
        </CardHeader>
        <CardContent className="space-y-6">
          {steps[step].content}

          <div className="flex justify-between">
            <Button
              variant="ghost"
              onClick={() => setStep((s) => s - 1)}
              disabled={step === 0}
            >
              <ChevronLeft className="mr-1 h-4 w-4" />
              이전
            </Button>

            {isLastStep ? (
              <Button onClick={handleSubmit} disabled={loading}>
                {loading ? "저장 중..." : "완료"}
                <Check className="ml-1 h-4 w-4" />
              </Button>
            ) : (
              <Button onClick={() => setStep((s) => s + 1)}>
                다음
                <ChevronRight className="ml-1 h-4 w-4" />
              </Button>
            )}
          </div>

          {!isLastStep && (
            <button
              className="block mx-auto text-sm text-muted-foreground hover:underline"
              onClick={() => router.push("/")}
            >
              건너뛰기
            </button>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
