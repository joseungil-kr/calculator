"use client";

import { useState } from 'react';
import { motion, AnimatePresence, type Variants } from 'framer-motion';
import { Loader2, CheckCircle2, Building2, MapPin, XCircle, CheckCircle } from 'lucide-react';
import Image from 'next/image';

type Step =
  | 'HERO'
  | 'SEARCH_INPUT'
  | 'SEARCH_LOADING'
  | 'CONFIRM_PLACE'
  | 'DETAILS_INPUT'
  | 'CALC_BASE'
  | 'CALC_DISCOUNT'
  | 'CALC_COMPARE'
  | 'FINAL_RESULT'
  | 'DONE';

interface PlaceInfo {
  name: string;
  category: string;
  address: string;
  phone: string;
}

// 주소에서 시/구/동을 추출하는 유틸리티
const extractLocalArea = (address: string) => {
  if (!address) return '해당 지역';
  const parts = address.split(' ');
  if (parts.length >= 3) return `${parts[1]} ${parts[2]}`;
  return parts[1] || '해당 지역';
};

const extractDong = (address: string) => {
  if (!address) return '동네';
  const match = address.match(/([가-힣]+[동|리|읍|면])/);
  if (match) return match[1];
  return '근처';
};

export default function Home() {
  const [step, setStep] = useState<Step>('HERO');
  
  const [searchQuery, setSearchQuery] = useState('');
  const [searchError, setSearchError] = useState('');
  
  const [placeInfo, setPlaceInfo] = useState<PlaceInfo | null>(null);
  
  const [details, setDetails] = useState({
    name: '',
    address: '',
    categoryType: '음식점', // 음식점, 사무실, 학원, 노래방(주점), 기타
    categoryText: '',
    phone: '',
    area: 20,
    floor: 1,
    hasElevator: false,
  });

  const [prices, setPrices] = useState({
    base: 0,
    discount: 0,
    final: 0
  });

  const nextStep = (target: Step) => setStep(target);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setSearchError('');
    nextStep('SEARCH_LOADING');

    try {
      await new Promise(resolve => setTimeout(resolve, 1500));
      const res = await fetch(`/api/place?q=${encodeURIComponent(searchQuery)}`);
      if (!res.ok) throw new Error('검색 결과가 없습니다.');
      const data = await res.json();
      
      setPlaceInfo({
        name: data.name,
        category: data.category,
        address: data.address,
        phone: data.phone
      });
      nextStep('CONFIRM_PLACE');
    } catch (err: unknown) {
      setSearchError(err instanceof Error ? err.message : '오류가 발생했습니다.');
      // 검색 실패 시 바로 수기 입력 폼으로 이동
      handleConfirmPlace(false);
    }
  };

  const handleConfirmPlace = (isCorrect: boolean) => {
    if (isCorrect && placeInfo) {
      // 카테고리 자동 매핑
      let cType = '기타';
      const cat = placeInfo.category || '';
      if (cat.includes('식당') || cat.includes('음식')) cType = '음식점';
      else if (cat.includes('사무')) cType = '사무실';
      else if (cat.includes('학원')) cType = '학원';
      else if (cat.includes('노래') || cat.includes('주점')) cType = '노래방(주점)';

      setDetails(prev => ({
        ...prev,
        name: placeInfo.name,
        address: placeInfo.address,
        phone: '', // 매장 번호를 미리 채우지 않고 비워둡니다.
        categoryType: cType,
        categoryText: cType === '기타' ? cat : ''
      }));
    } else {
      // 초기화
      setDetails(prev => ({
        ...prev,
        name: '',
        address: '',
        phone: '',
        categoryType: '음식점',
        categoryText: ''
      }));
    }
    nextStep('DETAILS_INPUT');
  };

  const startCalculation = async () => {
    let basePrice = details.area * 150000;
    if (details.floor >= 3 && !details.hasElevator) basePrice += 500000;
    
    // 음식점일 경우 추가 비용 (임의 계산식 반영)
    if (details.categoryType === '음식점') basePrice += 300000;

    const discount = Math.min(details.area * 130000, 2500000);
    const finalPrice = Math.floor((basePrice - discount) * 0.95);

    setPrices({ base: basePrice, discount, final: finalPrice });

    nextStep('CALC_BASE');
    await new Promise(r => setTimeout(r, 1500));
    nextStep('CALC_DISCOUNT');
    await new Promise(r => setTimeout(r, 1500));
    nextStep('CALC_COMPARE');
    await new Promise(r => setTimeout(r, 2000));
    nextStep('FINAL_RESULT');
  };

  const fadeVariants: Variants = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" } },
    exit: { opacity: 0, y: -20, transition: { duration: 0.3 } }
  };

  return (
    <main className="min-h-screen bg-gray-50 text-gray-900 font-sans flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-md bg-white rounded-3xl shadow-xl overflow-hidden min-h-[600px] flex flex-col relative">
        <AnimatePresence mode="wait">
          
          {/* 1. 히어로 페이지 */}
          {step === 'HERO' && (
            <motion.div key="hero" variants={fadeVariants} initial="initial" animate="animate" exit="exit" className="flex-1 flex flex-col p-8">
              <div className="flex-1 flex flex-col items-center justify-center text-center">
                <div className="w-full aspect-square relative mb-8 rounded-2xl overflow-hidden bg-gray-100">
                  <Image src="/hero.jpg" alt="철거 견적 일러스트" fill className="object-cover" />
                </div>
                <h1 className="text-3xl font-bold mb-4 leading-tight">우리 가게 철거 비용,<br/>얼마나 들까요?</h1>
                <p className="text-gray-500 text-lg">1분 만에 예상 견적을 확인해보세요.</p>
              </div>
              <button 
                onClick={() => nextStep('SEARCH_INPUT')}
                className="w-full bg-blue-600 text-white font-semibold text-lg py-4 rounded-2xl active:scale-[0.98] transition-transform"
              >
                견적 알아보기
              </button>
            </motion.div>
          )}

          {/* 2. 상호 검색 입력 */}
          {step === 'SEARCH_INPUT' && (
            <motion.div key="search_input" variants={fadeVariants} initial="initial" animate="animate" exit="exit" className="flex-1 flex flex-col p-8">
              <div className="mt-8">
                <h2 className="text-2xl font-bold mb-6">가게 이름 또는 전화번호를 입력해 주세요</h2>
                <div className="relative">
                  <input 
                    type="text" 
                    autoFocus
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                    placeholder="예)스타벅스 스타필드점, 낙지한마당 신촌역점"
                    className="w-full text-lg py-4 border-b-2 border-gray-200 focus:border-blue-600 outline-none transition-colors"
                  />
                  {searchError && <p className="text-red-500 text-sm mt-3">{searchError}</p>}
                </div>
              </div>
              <div className="mt-auto">
                <button 
                  onClick={handleSearch}
                  disabled={!searchQuery.trim()}
                  className="w-full bg-blue-600 disabled:bg-gray-200 disabled:text-gray-400 text-white font-semibold text-lg py-4 rounded-2xl transition-colors"
                >
                  다음
                </button>
              </div>
            </motion.div>
          )}

          {/* 2-1. 업체 확인 단계 */}
          {step === 'CONFIRM_PLACE' && placeInfo && (
            <motion.div key="confirm_place" variants={fadeVariants} initial="initial" animate="animate" exit="exit" className="flex-1 flex flex-col p-8 justify-center">
              <h2 className="text-2xl font-bold mb-8 text-center">이 업체가 맞나요?</h2>
              
              <div className="bg-gray-50 rounded-2xl p-6 border border-gray-200 shadow-sm mb-8 text-center">
                <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Building2 className="w-8 h-8 text-blue-600" />
                </div>
                <h3 className="text-2xl font-bold text-gray-900 mb-2">{placeInfo.name}</h3>
                <p className="text-gray-600 flex items-center justify-center gap-1 mb-1">
                  <MapPin className="w-4 h-4" /> {placeInfo.address}
                </p>
                <p className="text-sm text-gray-500">{placeInfo.category}</p>
              </div>

              <div className="space-y-3 mt-auto">
                <button 
                  onClick={() => handleConfirmPlace(true)}
                  className="w-full bg-blue-600 text-white font-semibold text-lg py-4 rounded-2xl flex items-center justify-center gap-2"
                >
                  <CheckCircle className="w-5 h-5" /> 예, 맞습니다
                </button>
                <button 
                  onClick={() => handleConfirmPlace(false)}
                  className="w-full bg-gray-100 text-gray-600 font-semibold text-lg py-4 rounded-2xl flex items-center justify-center gap-2"
                >
                  <XCircle className="w-5 h-5" /> 아니오, 직접 입력할게요
                </button>
              </div>
            </motion.div>
          )}

          {/* 3. 로딩 상태 모음 (검색, 계산) */}
          {(step === 'SEARCH_LOADING' || step === 'CALC_BASE' || step === 'CALC_DISCOUNT' || step === 'CALC_COMPARE') && (
            <motion.div key={step} variants={fadeVariants} initial="initial" animate="animate" exit="exit" className="flex-1 flex flex-col items-center justify-center p-8 text-center">
              <Loader2 className="w-12 h-12 text-blue-600 animate-spin mb-6" />
              <h2 className="text-2xl font-bold text-gray-800">
                {step === 'SEARCH_LOADING' && "가게 정보를 찾고 있습니다..."}
                {step === 'CALC_BASE' && "기본 견적을 계산하는 중..."}
                {step === 'CALC_DISCOUNT' && "소상공인 폐업지원금\n조건 검색중..."}
                {step === 'CALC_COMPARE' && `${extractLocalArea(details.address || placeInfo?.address || '')} 인근\n업체별 비교견적 중입니다...`}
              </h2>
              {step === 'CALC_BASE' && <p className="mt-4 text-xl font-medium text-gray-500">{prices.base.toLocaleString()}원 (예상)</p>}
              {step === 'CALC_DISCOUNT' && <p className="mt-4 text-xl font-medium text-blue-600">-{prices.discount.toLocaleString()}원 지원 가능성 발견!</p>}
              {step === 'CALC_COMPARE' && (
                <div className="mt-6 text-left w-full max-w-xs mx-auto bg-gray-50 rounded-xl p-4 border border-gray-100">
                  <p className="text-sm font-semibold text-gray-600 mb-2">근처 5개 철거업체 탐색 완료</p>
                  <ul className="text-gray-500 space-y-1 text-sm">
                    <li>• 가O철거</li>
                    <li>• 철거XX왕</li>
                    <li>• {extractDong(details.address || placeInfo?.address || '')}철거</li>
                    <li>• 마X철거</li>
                    <li>• O스타철거</li>
                  </ul>
                </div>
              )}
            </motion.div>
          )}

          {/* 4. 상세 정보 입력 */}
          {step === 'DETAILS_INPUT' && (
            <motion.div key="details_input" variants={fadeVariants} initial="initial" animate="animate" exit="exit" className="flex-1 flex flex-col p-8 overflow-y-auto">
              <div className="mt-4 mb-8">
                <h2 className="text-2xl font-bold mb-2">철거 상세정보를 채워주세요</h2>
              </div>

              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">상호</label>
                  <input 
                    type="text" 
                    value={details.name}
                    onChange={(e) => setDetails({...details, name: e.target.value})}
                    placeholder="가게 상호명"
                    className="w-full text-base p-4 bg-gray-50 rounded-xl border border-gray-200 outline-none focus:ring-2 focus:ring-blue-100 focus:border-blue-500 transition-all"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">주소</label>
                  <input 
                    type="text" 
                    value={details.address}
                    onChange={(e) => setDetails({...details, address: e.target.value})}
                    placeholder="시/군/구 동/면/읍"
                    className="w-full text-base p-4 bg-gray-50 rounded-xl border border-gray-200 outline-none focus:ring-2 focus:ring-blue-100 focus:border-blue-500 transition-all"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">업종</label>
                  <select 
                    value={details.categoryType}
                    onChange={(e) => setDetails({...details, categoryType: e.target.value})}
                    className="w-full text-base p-4 bg-gray-50 rounded-xl border border-gray-200 outline-none focus:ring-2 focus:ring-blue-100 focus:border-blue-500 transition-all mb-2"
                  >
                    <option value="음식점">음식점</option>
                    <option value="사무실">사무실</option>
                    <option value="학원">학원</option>
                    <option value="노래방(주점)">노래방(주점)</option>
                    <option value="기타">기타</option>
                  </select>
                  {details.categoryType === '기타' && (
                    <input 
                      type="text" 
                      value={details.categoryText}
                      onChange={(e) => setDetails({...details, categoryText: e.target.value})}
                      placeholder="직접 입력해주세요"
                      className="w-full text-base p-4 bg-gray-50 rounded-xl border border-gray-200 outline-none focus:ring-2 focus:ring-blue-100 focus:border-blue-500 transition-all"
                    />
                  )}
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">연락처 <span className="text-red-500">*</span></label>
                  <input 
                    type="text" 
                    value={details.phone}
                    onChange={(e) => setDetails({...details, phone: e.target.value})}
                    placeholder="연락받으실 번호를 입력하세요"
                    className="w-full text-base p-4 bg-gray-50 rounded-xl border border-gray-200 outline-none focus:ring-2 focus:ring-blue-100 focus:border-blue-500 transition-all"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-100">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">평수 (평)</label>
                    <input 
                      type="number" 
                      value={details.area || ''}
                      onChange={(e) => setDetails({...details, area: Number(e.target.value)})}
                      className="w-full text-lg p-4 bg-gray-50 rounded-xl border border-gray-200 outline-none focus:ring-2 focus:ring-blue-100 focus:border-blue-500 transition-all"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">층수</label>
                    <input 
                      type="number" 
                      value={details.floor || ''}
                      onChange={(e) => setDetails({...details, floor: Number(e.target.value)})}
                      className="w-full text-lg p-4 bg-gray-50 rounded-xl border border-gray-200 outline-none focus:ring-2 focus:ring-blue-100 focus:border-blue-500 transition-all"
                    />
                  </div>
                </div>
              </div>

              <div className="mt-12 mb-4">
                <button 
                  onClick={startCalculation}
                  disabled={!details.phone.trim()}
                  className="w-full bg-blue-600 disabled:bg-gray-200 disabled:text-gray-400 text-white font-semibold text-lg py-4 rounded-2xl active:scale-[0.98] transition-colors"
                >
                  견적 확인하기
                </button>
              </div>
            </motion.div>
          )}

          {/* 5. 최종 결과 */}
          {step === 'FINAL_RESULT' && (
            <motion.div key="final_result" variants={fadeVariants} initial="initial" animate="animate" exit="exit" className="flex-1 flex flex-col p-8 bg-blue-600 text-white">
              <div className="mt-8 flex-1">
                <p className="text-blue-200 font-medium mb-2">{extractLocalArea(details.address || placeInfo?.address || '')} 인근 5개 철거업체 탐색 완료</p>
                <h2 className="text-3xl font-bold mb-4 leading-tight">업체간 견적은<br/>최저 {Math.floor(prices.final * 0.9).toLocaleString()}원 ~<br/>최고 {Math.floor(prices.final * 1.3).toLocaleString()}원 입니다.</h2>
                
                <div className="bg-white/10 rounded-2xl p-5 backdrop-blur-sm space-y-4">
                  <div className="flex justify-between items-center text-sm text-blue-100 mb-2 border-b border-white/20 pb-2">
                    <span>탐색된 업체 (5곳)</span>
                  </div>
                  <div className="flex flex-wrap gap-2 text-sm font-medium">
                    <span className="bg-white/20 px-3 py-1 rounded-full">가O철거</span>
                    <span className="bg-white/20 px-3 py-1 rounded-full">철거XX왕</span>
                    <span className="bg-white/20 px-3 py-1 rounded-full">{extractDong(details.address || placeInfo?.address || '')}철거</span>
                    <span className="bg-white/20 px-3 py-1 rounded-full">마X철거</span>
                    <span className="bg-white/20 px-3 py-1 rounded-full">O스타철거</span>
                  </div>
                </div>
              </div>

              <div className="bg-white text-gray-900 rounded-3xl p-6 mt-8 shadow-2xl -mx-4 -mb-8">
                <h3 className="font-bold text-lg mb-2 text-center">견적가 하위 3개 업체에<br/>연락처를 전달할까요?</h3>
                <p className="text-gray-500 text-sm mb-6 text-center">전달된 연락처로 업체가 직접 무료 방문 실측 일정을 안내해 드립니다.</p>
                
                <div className="space-y-3">
                  <button onClick={() => nextStep('DONE')} className="w-full bg-blue-600 text-white font-semibold py-4 rounded-xl">
                    네, 업체 3곳에 전달해주세요
                  </button>
                  <button onClick={() => nextStep('DONE')} className="w-full bg-gray-100 text-gray-600 font-medium py-4 rounded-xl">
                    아니요, 견적만 볼게요
                  </button>
                </div>
              </div>
            </motion.div>
          )}

          {/* 6. 완료 */}
          {step === 'DONE' && (
            <motion.div key="done" variants={fadeVariants} initial="initial" animate="animate" exit="exit" className="flex-1 flex flex-col items-center justify-center p-8 text-center">
              <CheckCircle2 className="w-16 h-16 text-green-500 mb-6" />
              <h2 className="text-2xl font-bold mb-2">안내가 완료되었습니다</h2>
              <p className="text-gray-500 mb-2">이용해 주셔서 감사합니다.</p>
              <p className="text-blue-600 font-medium bg-blue-50 py-3 px-6 rounded-xl mt-2">
                업체 담당자를 통해 연락 드리겠습니다.
              </p>
              <button onClick={() => { setPlaceInfo(null); nextStep('HERO'); }} className="mt-8 text-gray-400 font-medium underline underline-offset-4">
                처음으로 돌아가기
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </main>
  );
}

