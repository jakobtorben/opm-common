#! /usr/bin/python3
#
# This script provides "hand loop-unrolled" specializations of the
# Evaluation class of dense automatic differentiation so that the
# compiler can more easily emit SIMD instructions. In an ideal world,
# C++ compilers should be smart enough to do this themselfs, but
# contemporary compilers don't seem to exhibit enough brains.
#
# Usage: In the opm-material top-level source directory, run
# `./bin/genEvalSpecializations.py [MAX_DERIVATIVES]`. The script then
# generates specializations for Evaluations with up to MAX_DERIVATIVES
# derivatives. The default for MAX_DERIVATIVES is 12. To run this
# script, you need a python 2 installation where the Jinja2 module is
# available.
#
import os
import sys
import jinja2

maxDerivs = 12
if len(sys.argv) == 2:
    maxDerivs = int(sys.argv[1])

specializationFileNames = []

specializationTemplate = \
"""// -*- mode: C++; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*-
// vi: set et ts=4 sw=4 sts=4:
/*
  This file is part of the Open Porous Media project (OPM).

  OPM is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 2 of the License, or
  (at your option) any later version.

  OPM is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with OPM.  If not, see <http://www.gnu.org/licenses/>.

  Consult the COPYING file in the top-level source directory of this
  module for the precise wording of the license and the list of
  copyright holders.
*/
/*!
 * \\file
 *
{% if numDerivs < 0 %}\
 * \\brief This file file provides a dense-AD Evaluation class where the
 *        number of derivatives is specified at runtime.
{% elif numDerivs == 0 %}\
 * \\brief Representation of an evaluation of a function and its derivatives w.r.t. a set
 *        of variables in the localized OPM automatic differentiation (AD) framework.
{% else %}\
 * \\brief This file specializes the dense-AD Evaluation class for {{ numDerivs }} derivatives.
{% endif %}\
 *
 * \\attention THIS FILE GETS AUTOMATICALLY GENERATED BY THE "{{ scriptName }}"
 *            SCRIPT. DO NOT EDIT IT MANUALLY!
 */
{% if numDerivs < 0 %}\
#ifndef OPM_DENSEAD_EVALUATION_DYNAMIC_HPP
#define OPM_DENSEAD_EVALUATION_DYNAMIC_HPP
{% elif numDerivs == 0 %}\
#ifndef OPM_DENSEAD_EVALUATION_HPP
#define OPM_DENSEAD_EVALUATION_HPP
{% else %}\
#ifndef OPM_DENSEAD_EVALUATION{{numDerivs}}_HPP
#define OPM_DENSEAD_EVALUATION{{numDerivs}}_HPP
{% endif %}\

#ifndef NDEBUG
#include <opm/material/common/Valgrind.hpp>
#endif
{% if numDerivs < 0 %}\
#include <opm/material/common/FastSmallVector.hpp>

{% else %}\

#include <array>
{% endif %}\
#include <cassert>
#include <iosfwd>
#include <stdexcept>

#include <opm/common/utility/gpuDecorators.hpp>

namespace Opm {
namespace DenseAd {

{% if numDerivs == 0 %}\
//! Indicates that the number of derivatives considered by an Evaluation object
//! is run-time determined
static constexpr int DynamicSize = -1;

{% endif %}\
{% if numDerivs < 0 %}\
/*!
 * \\brief Represents a function evaluation and its derivatives w.r.t. a
 *        run-time specified set of variables.
 */
template <class ValueT, unsigned staticSize>
class Evaluation<ValueT, DynamicSize, staticSize>
{% elif numDerivs == 0 %}\
/*!
 * \\brief Represents a function evaluation and its derivatives w.r.t. a fixed set of
 *        variables.
 */
template <class ValueT, int numDerivs, unsigned staticSize = 0>
class Evaluation
{% else %}\
template <class ValueT>
class Evaluation<ValueT, {{ numDerivs }}>
{% endif %}\
{
public:
    //! the template argument which specifies the number of
    //! derivatives (-1 == "DynamicSize" means runtime determined)
{% if numDerivs < 0 %}\
    static const int numVars = DynamicSize;
{% elif numDerivs > 0 %}\
    static const int numVars = {{ numDerivs }};
{% else %}\
    static const int numVars = numDerivs;
{% endif %}\

    //! field type
    typedef ValueT ValueType;

    //! number of derivatives
{% if numDerivs < 0 %}\
    OPM_HOST_DEVICE int size() const
    { return data_.size() - 1; }
{% elif numDerivs == 0 %}\
    OPM_HOST_DEVICE constexpr int size() const
    { return numDerivs; }
{% else %}\
    OPM_HOST_DEVICE constexpr int size() const
    { return {{ numDerivs }}; };
{% endif %}\

protected:
    //! length of internal data vector
{% if numDerivs < 0 %}\
    OPM_HOST_DEVICE int length_() const
    { return data_.size(); }
{% else %}\
    OPM_HOST_DEVICE constexpr int length_() const
    { return size() + 1; }
{% endif %}\


{% if numDerivs < 0 %}\
    //! position index for value
    OPM_HOST_DEVICE constexpr int valuepos_() const
    { return 0; }
    //! start index for derivatives
    OPM_HOST_DEVICE constexpr int dstart_() const
    { return 1; }
    //! end+1 index for derivatives
    OPM_HOST_DEVICE int dend_() const
    { return length_(); }
{% else %}\
    //! position index for value
    OPM_HOST_DEVICE constexpr int valuepos_() const
    { return 0; }
    //! start index for derivatives
    OPM_HOST_DEVICE constexpr int dstart_() const
    { return 1; }
    //! end+1 index for derivatives
    OPM_HOST_DEVICE constexpr int dend_() const
    { return length_(); }
{% endif %}\

    //! instruct valgrind to check that the value and all derivatives of the
    //! Evaluation object are well-defined.
    OPM_HOST_DEVICE constexpr void checkDefined_() const
    {
#ifndef NDEBUG
{% if numDerivs < 0 %}\
        for (int i = dstart_(); i < dend_(); ++i)
            Valgrind::CheckDefined(data_[i]);
{% else %}\
       for (const auto& v: data_)
           Valgrind::CheckDefined(v);
{% endif %}\
#endif
    }

public:
    //! default constructor
    OPM_HOST_DEVICE Evaluation() : data_()
    {}

    //! copy other function evaluation
    Evaluation(const Evaluation& other) = default;

{% if numDerivs < 0 %}\
    //! move other function evaluation (this only makes sense for dynamically
    //! allocated Evaluations)
    OPM_HOST_DEVICE Evaluation(Evaluation&& other)
        : data_(std::move(other.data_))
    { }

    //! move assignment
    OPM_HOST_DEVICE Evaluation& operator=(Evaluation&& other)
    {
        data_ = std::move(other.data_);
        return *this;
    }
{% endif %}\

{% if numDerivs < 0 %}\
    // create a "blank" dynamic evaluation
    OPM_HOST_DEVICE explicit Evaluation(int numDerivatives)
        : data_(1 + numDerivatives)
    {}

    // create a dynamic evaluation which represents a constant function
    //
    // i.e., f(x) = c. this implies an evaluation with the given value and all
    // derivatives being zero.
    template <class RhsValueType>
    OPM_HOST_DEVICE Evaluation(int numDerivatives, const RhsValueType& c)
        : data_(1 + numDerivatives, 0.0)
    {
        //clearDerivatives();
        setValue(c);

        checkDefined_();
    }
{% else %}\
    // create an evaluation which represents a constant function
    //
    // i.e., f(x) = c. this implies an evaluation with the given value and all
    // derivatives being zero.
    template <class RhsValueType>
    OPM_HOST_DEVICE constexpr Evaluation(const RhsValueType& c): data_{}
    {
        setValue(c);
        clearDerivatives();

        //checkDefined_();
    }
{% endif %}\

    // create an evaluation which represents a constant function
    //
    // i.e., f(x) = c. this implies an evaluation with the given value and all
    // derivatives being zero.
{% if numDerivs < 0 %}\
    template <class RhsValueType>
    OPM_HOST_DEVICE Evaluation(int nVars, const RhsValueType& c, int varPos)
     : data_(1 + nVars, 0.0)
    {
        // The variable position must be in represented by the given variable descriptor
        assert(0 <= varPos && varPos < size());

        setValue(c);

        data_[varPos + dstart_()] = 1.0;

        checkDefined_();
    }
{% else %}\
    template <class RhsValueType>
    OPM_HOST_DEVICE Evaluation(const RhsValueType& c, int varPos)
    {
        // The variable position must be in represented by the given variable descriptor
        assert(0 <= varPos && varPos < size());

        setValue( c );
        clearDerivatives();

        data_[varPos + dstart_()] = 1.0;

        checkDefined_();
    }
{% endif %}\

    // set all derivatives to zero
    OPM_HOST_DEVICE constexpr void clearDerivatives()
    {
{% if numDerivs <= 0 %}\
        for (int i = dstart_(); i < dend_(); ++i)
            data_[i] = 0.0;
{% else %}\
{%   for i in range(1, numDerivs+1) %}\
        data_[{{i}}] = 0.0;
{%   endfor %}\
{% endif %}\
    }

    // create an uninitialized Evaluation object that is compatible with the
    // argument, but not initialized
    //
    // This basically boils down to the copy constructor without copying
    // anything. If the number of derivatives is known at compile time, this
    // is equivalent to creating an uninitialized object using the default
    // constructor, while for dynamic evaluations, it creates an Evaluation
    // object which exhibits the same number of derivatives as the argument.
{% if numDerivs < 0 %}\
    OPM_HOST_DEVICE static Evaluation createBlank(const Evaluation& x)
    { return Evaluation(x.size()); }
{% else %}\
    OPM_HOST_DEVICE static Evaluation createBlank(const Evaluation&)
    { return Evaluation(); }
{% endif %}\

    // create an Evaluation with value and all the derivatives to be zero
{% if numDerivs < 0 %}\
    OPM_HOST_DEVICE static Evaluation createConstantZero(const Evaluation& x)
    { return Evaluation(x.size(), 0.0); }
{% else %}\
    OPM_HOST_DEVICE static Evaluation createConstantZero(const Evaluation&)
    { return Evaluation(0.); }
{% endif %}\

    // create an Evaluation with value to be one and all the derivatives to be zero
{% if numDerivs < 0 %}\
    OPM_HOST_DEVICE static Evaluation createConstantOne(const Evaluation& x)
    { return Evaluation(x.size(), 1.); }
{% else %}\
    OPM_HOST_DEVICE static Evaluation createConstantOne(const Evaluation&)
    { return Evaluation(1.); }
{% endif %}\

    // create a function evaluation for a "naked" depending variable (i.e., f(x) = x)
{% if numDerivs < 0 %}\
    template <class RhsValueType>
    OPM_HOST_DEVICE static Evaluation createVariable(const RhsValueType&, int)
    {
        throw std::logic_error("Dynamically sized evaluations require that the number of "
                               "derivatives is specified when creating an evaluation");
    }

    template <class RhsValueType>
    OPM_HOST_DEVICE static Evaluation createVariable(int nVars, const RhsValueType& value, int varPos)
    {
        // copy function value and set all derivatives to 0, except for the variable
        // which is represented by the value (which is set to 1.0)
        return Evaluation(nVars, value, varPos);
    }

    template <class RhsValueType>
    OPM_HOST_DEVICE static Evaluation createVariable(const Evaluation& x, const RhsValueType& value, int varPos)
    {
        // copy function value and set all derivatives to 0, except for the variable
        // which is represented by the value (which is set to 1.0)
        return Evaluation(x.size(), value, varPos);
    }
{% else %}\
    template <class RhsValueType>
    OPM_HOST_DEVICE static Evaluation createVariable(const RhsValueType& value, int varPos)
    {
        // copy function value and set all derivatives to 0, except for the variable
        // which is represented by the value (which is set to 1.0)
        return Evaluation(value, varPos);
    }

    template <class RhsValueType>
    OPM_HOST_DEVICE static Evaluation createVariable(int nVars, const RhsValueType& value, int varPos)
    {
        if (nVars != {{numDerivs}})
            throw std::logic_error("This statically-sized evaluation can only represent objects"
                                   " with {{numDerivs}} derivatives");

        // copy function value and set all derivatives to 0, except for the variable
        // which is represented by the value (which is set to 1.0)
        return Evaluation(nVars, value, varPos);
    }

    template <class RhsValueType>
    OPM_HOST_DEVICE static Evaluation createVariable(const Evaluation&, const RhsValueType& value, int varPos)
    {
        // copy function value and set all derivatives to 0, except for the variable
        // which is represented by the value (which is set to 1.0)
        return Evaluation(value, varPos);
    }
{% endif %}\


{% if numDerivs < 0 %}\
    // "evaluate" a constant function (i.e. a function that does not depend on the set of
    // relevant variables, f(x) = c).
    template <class RhsValueType>
    OPM_HOST_DEVICE static Evaluation createConstant(int nVars, const RhsValueType& value)
    {
        return Evaluation(nVars, value);
    }

    // "evaluate" a constant function (i.e. a function that does not depend on the set of
    // relevant variables, f(x) = c).
    template <class RhsValueType>
    OPM_HOST_DEVICE static Evaluation createConstant(const RhsValueType&)
    {
        throw std::logic_error("Dynamically-sized evaluation objects require to specify the number of derivatives.");
    }

    // "evaluate" a constant function (i.e. a function that does not depend on the set of
    // relevant variables, f(x) = c).
    template <class RhsValueType>
    OPM_HOST_DEVICE static Evaluation createConstant(const Evaluation& x, const RhsValueType& value)
    {
        return Evaluation(x.size(), value);
    }
{% else %}\
    // "evaluate" a constant function (i.e. a function that does not depend on the set of
    // relevant variables, f(x) = c).
    template <class RhsValueType>
    OPM_HOST_DEVICE static Evaluation createConstant(int nVars, const RhsValueType& value)
    {
        if (nVars != {{numDerivs}})
            throw std::logic_error("This statically-sized evaluation can only represent objects"
                                   " with {{numDerivs}} derivatives");
        return Evaluation(value);
    }

    // "evaluate" a constant function (i.e. a function that does not depend on the set of
    // relevant variables, f(x) = c).
    template <class RhsValueType>
    OPM_HOST_DEVICE static Evaluation createConstant(const RhsValueType& value)
    {
        return Evaluation(value);
    }

    // "evaluate" a constant function (i.e. a function that does not depend on the set of
    // relevant variables, f(x) = c).
    template <class RhsValueType>
    OPM_HOST_DEVICE static Evaluation createConstant(const Evaluation&, const RhsValueType& value)
    {
        return Evaluation(value);
    }
{% endif %}\

    // copy all derivatives from other
    OPM_HOST_DEVICE void copyDerivatives(const Evaluation& other)
    {
        assert(size() == other.size());

{% if numDerivs <= 0 %}\
        for (int i = dstart_(); i < dend_(); ++i)
            data_[i] = other.data_[i];
{% else %}\
{%   for i in range(1, numDerivs+1) %}\
        data_[{{i}}] = other.data_[{{i}}];
{%   endfor %}\
{% endif %}\
    }


    // add value and derivatives from other to this values and derivatives
    OPM_HOST_DEVICE Evaluation& operator+=(const Evaluation& other)
    {
        assert(size() == other.size());

{% if numDerivs <= 0 %}\
        for (int i = 0; i < length_(); ++i)
            data_[i] += other.data_[i];
{% else %}\
{%   for i in range(0, numDerivs+1) %}\
        data_[{{i}}] += other.data_[{{i}}];
{%   endfor %}\
{% endif %}\

        return *this;
    }

    // add value from other to this values
    template <class RhsValueType>
    OPM_HOST_DEVICE Evaluation& operator+=(const RhsValueType& other)
    {
        // value is added, derivatives stay the same
        data_[valuepos_()] += other;

        return *this;
    }

    // subtract other's value and derivatives from this values
    OPM_HOST_DEVICE Evaluation& operator-=(const Evaluation& other)
    {
        assert(size() == other.size());

{% if numDerivs <= 0 %}\
        for (int i = 0; i < length_(); ++i)
            data_[i] -= other.data_[i];
{% else %}\
{%   for i in range(0, numDerivs+1) %}\
        data_[{{i}}] -= other.data_[{{i}}];
{%   endfor %}\
{% endif %}\

        return *this;
    }

    // subtract other's value from this values
    template <class RhsValueType>
    OPM_HOST_DEVICE Evaluation& operator-=(const RhsValueType& other)
    {
        // for constants, values are subtracted, derivatives stay the same
        data_[valuepos_()] -= other;

        return *this;
    }

    // multiply values and apply chain rule to derivatives: (u*v)' = (v'u + u'v)
    OPM_HOST_DEVICE Evaluation& operator*=(const Evaluation& other)
    {
        assert(size() == other.size());

        // while the values are multiplied, the derivatives follow the product rule,
        // i.e., (u*v)' = (v'u + u'v).
        const ValueType u = this->value();
        const ValueType v = other.value();

        // value
        data_[valuepos_()] *= v ;

        //  derivatives
{% if numDerivs <= 0 %}\
        for (int i = dstart_(); i < dend_(); ++i)
            data_[i] = data_[i] * v + other.data_[i] * u;
{% else %}\
{%   for i in range(1, numDerivs+1) %}\
        data_[{{i}}] = data_[{{i}}] * v + other.data_[{{i}}] * u;
{%   endfor %}\
{% endif %}\

        return *this;
    }

    // m(c*u)' = c*u'
    template <class RhsValueType>
    OPM_HOST_DEVICE Evaluation& operator*=(const RhsValueType& other)
    {
{% if numDerivs <= 0 %}\
        for (int i = 0; i < length_(); ++i)
            data_[i] *= other;
{% else %}\
{%   for i in range(0, numDerivs+1) %}\
        data_[{{i}}] *= other;
{%   endfor %}\
{% endif %}\

        return *this;
    }

    // m(u*v)' = (vu' - uv')/v^2
    OPM_HOST_DEVICE Evaluation& operator/=(const Evaluation& other)
    {
        assert(size() == other.size());

        // values are divided, derivatives follow the rule for division, i.e., (u/v)' = (v'u -
        // u'v)/v^2.
        ValueType& u = data_[valuepos_()];
        const ValueType& v = other.value();
{% if numDerivs <= 0 %}\
        for (int idx = dstart_(); idx < dend_(); ++idx) {
            const ValueType& uPrime = data_[idx];
            const ValueType& vPrime = other.data_[idx];

            data_[idx] = (v*uPrime - u*vPrime)/(v*v);
        }
{% else %}\
{%   for i in range(1, numDerivs+1) %}\
        data_[{{i}}] = (v*data_[{{i}}] - u*other.data_[{{i}}])/(v*v);
{%   endfor %}\
{% endif %}\
        u /= v;

        return *this;
    }

    // divide value and derivatives by value of other
    template <class RhsValueType>
    OPM_HOST_DEVICE Evaluation& operator/=(const RhsValueType& other)
    {
        const ValueType tmp = 1.0/other;

{% if numDerivs <= 0 %}\
        for (int i = 0; i < length_(); ++i)
            data_[i] *= tmp;
{% else %}\
{%   for i in range(0, numDerivs+1) %}\
        data_[{{i}}] *= tmp;
{%   endfor %}\
{% endif %}\

        return *this;
    }

    // add two evaluation objects
    OPM_HOST_DEVICE Evaluation operator+(const Evaluation& other) const
    {
        assert(size() == other.size());

        Evaluation result(*this);

        result += other;

        return result;
    }

    // add constant to this object
    template <class RhsValueType>
    OPM_HOST_DEVICE Evaluation operator+(const RhsValueType& other) const
    {
        Evaluation result(*this);

        result += other;

        return result;
    }

    // subtract two evaluation objects
    OPM_HOST_DEVICE Evaluation operator-(const Evaluation& other) const
    {
        assert(size() == other.size());

        Evaluation result(*this);

        result -= other;

        return result;
    }

    // subtract constant from evaluation object
    template <class RhsValueType>
    OPM_HOST_DEVICE Evaluation operator-(const RhsValueType& other) const
    {
        Evaluation result(*this);

        result -= other;

        return result;
    }

    // negation (unary minus) operator
    OPM_HOST_DEVICE Evaluation operator-() const
    {
{% if numDerivs < 0 %}\
        Evaluation result(*this);
{% else %}\
        Evaluation result;
{% endif %}\

        // set value and derivatives to negative
{% if numDerivs <= 0 %}\
        for (int i = 0; i < length_(); ++i)
            result.data_[i] = - data_[i];
{% else %}\
{%   for i in range(0, numDerivs+1) %}\
        result.data_[{{i}}] = - data_[{{i}}];
{%   endfor %}\
{% endif %}\

        return result;
    }

    OPM_HOST_DEVICE Evaluation operator*(const Evaluation& other) const
    {
        assert(size() == other.size());

        Evaluation result(*this);

        result *= other;

        return result;
    }

    template <class RhsValueType>
    OPM_HOST_DEVICE Evaluation operator*(const RhsValueType& other) const
    {
        Evaluation result(*this);

        result *= other;

        return result;
    }

    OPM_HOST_DEVICE Evaluation operator/(const Evaluation& other) const
    {
        assert(size() == other.size());

        Evaluation result(*this);

        result /= other;

        return result;
    }

    template <class RhsValueType>
    OPM_HOST_DEVICE Evaluation operator/(const RhsValueType& other) const
    {
        Evaluation result(*this);

        result /= other;

        return result;
    }

    template <class RhsValueType>
    OPM_HOST_DEVICE Evaluation& operator=(const RhsValueType& other)
    {
        setValue( other );
        clearDerivatives();

        return *this;
    }

    // copy assignment from evaluation
    Evaluation& operator=(const Evaluation& other) = default;

    template <class RhsValueType>
    OPM_HOST_DEVICE bool operator==(const RhsValueType& other) const
    { return value() == other; }

    OPM_HOST_DEVICE bool operator==(const Evaluation& other) const
    {
        assert(size() == other.size());

        for (int idx = 0; idx < length_(); ++idx) {
            if (data_[idx] != other.data_[idx]) {
                return false;
            }
        }
        return true;
    }

    OPM_HOST_DEVICE bool operator!=(const Evaluation& other) const
    { return !operator==(other); }

    template <class RhsValueType>
    OPM_HOST_DEVICE bool operator!=(const RhsValueType& other) const
    { return !operator==(other); }

    template <class RhsValueType>
    OPM_HOST_DEVICE bool operator>(RhsValueType other) const
    { return value() > other; }

    OPM_HOST_DEVICE bool operator>(const Evaluation& other) const
    {
        assert(size() == other.size());

        return value() > other.value();
    }

    template <class RhsValueType>
    OPM_HOST_DEVICE bool operator<(RhsValueType other) const
    { return value() < other; }

    OPM_HOST_DEVICE bool operator<(const Evaluation& other) const
    {
        assert(size() == other.size());

        return value() < other.value();
    }

    template <class RhsValueType>
    OPM_HOST_DEVICE bool operator>=(RhsValueType other) const
    { return value() >= other; }

    OPM_HOST_DEVICE bool operator>=(const Evaluation& other) const
    {
        assert(size() == other.size());

        return value() >= other.value();
    }

    template <class RhsValueType>
    OPM_HOST_DEVICE bool operator<=(RhsValueType other) const
    { return value() <= other; }

    OPM_HOST_DEVICE bool operator<=(const Evaluation& other) const
    {
        assert(size() == other.size());

        return value() <= other.value();
    }

    // return value of variable
    OPM_HOST_DEVICE const ValueType& value() const
    { return data_[valuepos_()]; }

    // set value of variable
    template <class RhsValueType>
    OPM_HOST_DEVICE constexpr void setValue(const RhsValueType& val)
    { data_[valuepos_()] = val; }

    // return varIdx'th derivative
    OPM_HOST_DEVICE const ValueType& derivative(int varIdx) const
    {
        assert(0 <= varIdx && varIdx < size());

        return data_[dstart_() + varIdx];
    }

    // set derivative at position varIdx
    OPM_HOST_DEVICE void setDerivative(int varIdx, const ValueType& derVal)
    {
        assert(0 <= varIdx && varIdx < size());

        data_[dstart_() + varIdx] = derVal;
    }

    template<class Serializer>
    OPM_HOST_DEVICE void serializeOp(Serializer& serializer)
    {
        serializer(data_);
    }

private:
{% if numDerivs < 0 %}\
    FastSmallVector<ValueT, staticSize> data_;
{% elif numDerivs == 0 %}\
    std::array<ValueT, numDerivs + 1> data_;
{% else %}\
    std::array<ValueT, {{numDerivs + 1}}> data_;
{% endif %}\
};

{% if numDerivs == 0 %}\
// the generic operators are only required for the unspecialized case
template <class RhsValueType, class ValueType, int numVars, unsigned staticSize>
OPM_HOST_DEVICE bool operator<(const RhsValueType& a, const Evaluation<ValueType, numVars, staticSize>& b)
{ return b > a; }

template <class RhsValueType, class ValueType, int numVars, unsigned staticSize>
OPM_HOST_DEVICE bool operator>(const RhsValueType& a, const Evaluation<ValueType, numVars, staticSize>& b)
{ return b < a; }

template <class RhsValueType, class ValueType, int numVars, unsigned staticSize>
OPM_HOST_DEVICE bool operator<=(const RhsValueType& a, const Evaluation<ValueType, numVars, staticSize>& b)
{ return b >= a; }

template <class RhsValueType, class ValueType, int numVars, unsigned staticSize>
OPM_HOST_DEVICE bool operator>=(const RhsValueType& a, const Evaluation<ValueType, numVars, staticSize>& b)
{ return b <= a; }

template <class RhsValueType, class ValueType, int numVars, unsigned staticSize>
OPM_HOST_DEVICE bool operator!=(const RhsValueType& a, const Evaluation<ValueType, numVars, staticSize>& b)
{ return a != b.value(); }

template <class RhsValueType, class ValueType, int numVars, unsigned staticSize>
OPM_HOST_DEVICE Evaluation<ValueType, numVars, staticSize> operator+(const RhsValueType& a, const Evaluation<ValueType, numVars, staticSize>& b)
{
    Evaluation<ValueType, numVars, staticSize> result(b);
    result += a;
    return result;
}

template <class RhsValueType, class ValueType, int numVars, unsigned staticSize>
OPM_HOST_DEVICE Evaluation<ValueType, numVars, staticSize> operator-(const RhsValueType& a, const Evaluation<ValueType, numVars, staticSize>& b)
{
    return -(b - a);
}

template <class RhsValueType, class ValueType, int numVars, unsigned staticSize>
OPM_HOST_DEVICE Evaluation<ValueType, numVars, staticSize> operator/(const RhsValueType& a, const Evaluation<ValueType, numVars, staticSize>& b)
{
    Evaluation<ValueType, numVars, staticSize> tmp(a);
    tmp /= b;
    return tmp;
}

template <class RhsValueType, class ValueType, int numVars, unsigned staticSize>
OPM_HOST_DEVICE Evaluation<ValueType, numVars, staticSize> operator*(const RhsValueType& a, const Evaluation<ValueType, numVars, staticSize>& b)
{
    Evaluation<ValueType, numVars, staticSize> result(b);
    result *= a;
    return result;
}

template<class T>
struct is_evaluation
{
    static constexpr bool value = false;
};

template <class ValueType, int numVars, unsigned staticSize>
struct is_evaluation<Evaluation<ValueType,numVars,staticSize>>
{
    static constexpr bool value = true;
};

template <class ValueType, int numVars, unsigned staticSize>
OPM_HOST_DEVICE void printEvaluation(std::ostream& os,
                     const Evaluation<ValueType, numVars, staticSize>& eval,
                     bool withDer = false);

template <class ValueType, int numVars, unsigned staticSize>
OPM_HOST_DEVICE std::ostream& operator<<(std::ostream& os, const Evaluation<ValueType, numVars, staticSize>& eval)
{
    if constexpr (is_evaluation<ValueType>::value)
        printEvaluation(os, eval.value(), false);
    else
        printEvaluation(os, eval, true);

    return os;
}

{% endif %}\
{% if numDerivs < 0 %}\
template <class Scalar, unsigned staticSize = 0>
using DynamicEvaluation = Evaluation<Scalar, DynamicSize, staticSize>;

{% endif %}\
} // namespace DenseAd
{% if numDerivs < 0 %}\

template <class Scalar, unsigned staticSize>
OPM_HOST_DEVICE DenseAd::Evaluation<Scalar, -1, staticSize> constant(int numDerivatives, const Scalar& value)
{ return DenseAd::Evaluation<Scalar, -1, staticSize>::createConstant(numDerivatives, value); }

template <class Scalar, unsigned staticSize>
OPM_HOST_DEVICE DenseAd::Evaluation<Scalar, -1, staticSize> variable(int numDerivatives, const Scalar& value, unsigned idx)
{ return DenseAd::Evaluation<Scalar, -1, staticSize>::createVariable(numDerivatives, value, idx); }

{% endif %}\
} // namespace Opm

{% if numDerivs == 0 %}\
#include "EvaluationSpecializations.hpp"

#endif // OPM_DENSEAD_EVALUATION_HPP
{% elif numDerivs < 0 %}\
#endif // OPM_DENSEAD_EVALUATION_DYNAMIC_HPP
{% else %}\
#endif // OPM_DENSEAD_EVALUATION{{numDerivs}}_HPP
{% endif %}\
"""

includeSpecializationsTemplate = \
"""// -*- mode: C++; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*-
// vi: set et ts=4 sw=4 sts=4:
/*
  This file is part of the Open Porous Media project (OPM).

  OPM is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 2 of the License, or
  (at your option) any later version.

  OPM is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with OPM.  If not, see <http://www.gnu.org/licenses/>.

  Consult the COPYING file in the top-level source directory of this
  module for the precise wording of the license and the list of
  copyright holders.
*/
/*!
 * \\file
 *
 * \\brief This file includes all specializations for the dense-AD Evaluation class.
 *
 * \\attention THIS FILE GETS AUTOMATICALLY GENERATED BY THE "{{ scriptName }}"
 *            SCRIPT. DO NOT EDIT IT MANUALLY!
 */
#ifndef OPM_DENSEAD_EVALUATION_SPECIALIZATIONS_HPP
#define OPM_DENSEAD_EVALUATION_SPECIALIZATIONS_HPP

{% for fileName in specializationFileNames %}\
#include <{{ fileName }}>
{% endfor %}\

#endif // OPM_DENSEAD_EVALUATION_SPECIALIZATIONS_HPP
"""

print ("Generating generic template classes")
fileName = "opm/material/densead/Evaluation.hpp"
template = jinja2.Template(specializationTemplate)
fileContents = template.render(numDerivs=0, scriptName=os.path.basename(sys.argv[0]))

f = open(fileName, "w")
f.write(fileContents)
f.close()

fileName = "opm/material/densead/DynamicEvaluation.hpp"
specializationFileNames.append(fileName)
fileContents = template.render(numDerivs=-1, scriptName=os.path.basename(sys.argv[0]))

f = open(fileName, "w")
f.write(fileContents)
f.close()

for numDerivs in range(1, maxDerivs + 1):
    print ("Generating specialization for %d derivatives"%numDerivs)

    fileName = "opm/material/densead/Evaluation%d.hpp"%numDerivs
    specializationFileNames.append(fileName)

    template = jinja2.Template(specializationTemplate)
    fileContents = template.render(numDerivs=numDerivs, scriptName=os.path.basename(sys.argv[0]))

    f = open(fileName, "w")
    f.write(fileContents)
    f.close()

template = jinja2.Template(includeSpecializationsTemplate)
fileContents = template.render(specializationFileNames=specializationFileNames, scriptName=os.path.basename(sys.argv[0]))

f = open("opm/material/densead/EvaluationSpecializations.hpp", "w")
f.write(fileContents)
f.close()
