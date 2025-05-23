/*
  Copyright 2020 Equinor ASA.

  This file is part of the Open Porous Media project (OPM).

  OPM is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  OPM is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with OPM.  If not, see <http://www.gnu.org/licenses/>.
*/

#include <opm/input/eclipse/EclipseState/SimulationConfig/RockConfig.hpp>

#include <opm/input/eclipse/EclipseState/Grid/FieldPropsManager.hpp>
#include <opm/input/eclipse/EclipseState/Tables/FlatTable.hpp>

#include <opm/input/eclipse/Deck/Deck.hpp>

#include <opm/input/eclipse/Parser/ParserKeywords/D.hpp>
#include <opm/input/eclipse/Parser/ParserKeywords/R.hpp>

#include <stdexcept>
#include <string>
#include <unordered_set>

namespace {

std::string num_prop(const std::string& prop_name)
{
    static const std::unordered_set<std::string> prop_names = {"PVTNUM", "SATNUM", "ROCKNUM"};
    if (prop_names.count(prop_name) == 1) {
        return prop_name;
    }

    throw std::invalid_argument("The rocknum propertype: " + prop_name + " is not valid");
}

bool refpres_prop(const std::string& prop_name)
{
    static const std::unordered_set<std::string> prop_names = {"NOSTORE", "STORE"};
    if (prop_names.count(prop_name) == 1) {
        bool store = prop_name == "STORE";
        return store;
    }

    throw std::invalid_argument("ROCKOPTS item 2 = " + prop_name + " is not valid");
}

Opm::RockConfig::Hysteresis hysteresis(const std::string& s)
{
    if (s == "REVERS")
        return Opm::RockConfig::Hysteresis::REVERS;

    if (s == "IRREVERS")
        return Opm::RockConfig::Hysteresis::IRREVERS;

    if (s == "HYSTER")
        return Opm::RockConfig::Hysteresis::HYSTER;

    if (s == "BOBERG")
        return Opm::RockConfig::Hysteresis::BOBERG;

    if (s == "REVLIMIT")
        return Opm::RockConfig::Hysteresis::REVLIMIT;

    if (s == "PALM-MAN")
        return Opm::RockConfig::Hysteresis::PALM_MAN;

    if (s == "NONE")
        return Opm::RockConfig::Hysteresis::NONE;

    throw std::invalid_argument("Not recognized hysteresis option: " + s);
}

} // Anonymous namespace

// ===========================================================================

namespace Opm {

RockConfig::RockComp::RockComp(double pref_arg, double comp_arg)
    : pref(pref_arg)
    , compressibility(comp_arg)
{}

bool RockConfig::RockComp::operator==(const RockConfig::RockComp& other) const
{
    return (this->pref == other.pref)
        && (this->compressibility == other.compressibility);
}

// ---------------------------------------------------------------------------

RockConfig::RockConfig()
    : num_property(ParserKeywords::ROCKOPTS::TABLE_TYPE::defaultValue)
    , num_tables  (ParserKeywords::ROCKCOMP::NTROCC::defaultValue)
{}

RockConfig::RockConfig(const Deck& deck, const FieldPropsManager& fp)
    : RockConfig {}
{
    using rock = ParserKeywords::ROCK;
    using rockopts = ParserKeywords::ROCKOPTS;
    using rockcomp = ParserKeywords::ROCKCOMP;
    using disperc = ParserKeywords::DISPERC;

    if (deck.hasKeyword<rock>()) {
        for (const auto& table : RockTable { deck.get<rock>().back() }) {
            this->m_comp.emplace_back(table.reference_pressure,
                                      table.compressibility);
        }
    }

    if (deck.hasKeyword<rockopts>()) {
        const auto& record = deck.get<rockopts>().back().getRecord(0);
        this->num_property = num_prop( record.getItem<rockopts::TABLE_TYPE>().getTrimmedString(0) );
        this->m_store = refpres_prop( record.getItem<rockopts::REF_PRESSURE>().getTrimmedString(0) );
    }

    if (deck.hasKeyword<rockcomp>()) {
        const auto& record = deck.get<rockcomp>().back().getRecord(0);
        if (fp.has_int("ROCKNUM")) {
            this->num_property = "ROCKNUM";
        }

        this->num_tables = record.getItem<rockcomp::NTROCC>().get<int>(0);
        this->hyst_mode = hysteresis(record.getItem<rockcomp::HYSTERESIS>().getTrimmedString(0));
        this->m_water_compaction = DeckItem::to_bool(record.getItem<rockcomp::WATER_COMPACTION>().getTrimmedString(0));

        this->m_active = true;
        if ((this->hyst_mode == Hysteresis::NONE) && !this->m_water_compaction) {
            this->m_active = false;
        }
    }

    if (deck.hasKeyword<disperc>()) {
        this->m_dispersion = true;
    }
}

RockConfig RockConfig::serializationTestObject()
{
    RockConfig result;
    result.m_active = true;
    result.m_comp = {{100, 0.25}, {200, 0.30}};
    result.num_property = "ROCKNUM";
    result.num_tables = 10;
    result.m_store = false;
    result.m_water_compaction = false;
    result.hyst_mode = Hysteresis::HYSTER;
    result.m_dispersion = false;

    return result;
}

bool RockConfig::active() const
{
    return this->m_active;
}

const std::vector<RockConfig::RockComp>& RockConfig::comp() const
{
    return this->m_comp;
}

const std::string& RockConfig::rocknum_property() const
{
    return this->num_property;
}

std::size_t RockConfig::num_rock_tables() const
{
    return this->num_tables;
}

RockConfig::Hysteresis RockConfig::hysteresis_mode() const
{
    return this->hyst_mode;
}

bool RockConfig::store() const
{
    return this->m_store;
}

bool RockConfig::water_compaction() const
{
    return this->m_water_compaction;
}

bool RockConfig::dispersion() const
{
    return this->m_dispersion;
}

bool RockConfig::operator==(const RockConfig& other) const
{
    return (this->num_property == other.num_property)
        && (this->m_comp == other.m_comp)
        && (this->num_tables == other.num_tables)
        && (this->m_active == other.m_active)
        && (this->m_store == other.m_store)
        && (this->m_water_compaction == other.m_water_compaction)
        && (this->hyst_mode == other.hyst_mode)
        && (this->m_dispersion == other.m_dispersion);
}

} //namespace Opm
